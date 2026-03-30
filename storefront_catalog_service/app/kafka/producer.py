"""
Base Kafka Producer implementation.

Provides a production-ready producer that:
- Uses Pydantic schemas for message validation
- Handles serialization automatically
- Supports delivery reports and retries
- Works with multi-broker clusters
- Implements exactly-once semantics (idempotence)
"""

import logging
import threading
from typing import Any, ClassVar

from django.conf import settings

from confluent_kafka import KafkaError, KafkaException, Producer
from confluent_kafka import Message as KafkaMessage
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KafkaPublisherException(Exception):
    """Raised when message publishing fails."""


class BaseKafkaProducer[SchemaT: BaseModel]:
    """
    Base class for Kafka producers with Pydantic schema support.

    Features:
    - Schema validation via Pydantic
    - Automatic JSON serialization
    - Delivery confirmation callbacks
    - Support for multi-broker clusters
    - Production-ready configuration (acks=all, idempotence)

    Usage:
        class OTPNotificationProducer(BaseKafkaProducer[OTPNotificationSchema]):
            topic = "notifications.otp"
            schema = OTPNotificationSchema

        producer = create_producer(OTPNotificationProducer)
        producer.publish({"phone": "+380...", "code": "1234"})
    """

    topic: ClassVar[str]
    schema: ClassVar[type[BaseModel]]

    _producer: Producer | None = None
    _lock: threading.Lock

    def __init__(self, config: dict[str, Any], transport: Any = None) -> None:
        """
        Initialize the producer.

        Args:
            config: Kafka configuration dict (bootstrap.servers, acks, etc.)
            transport: Optional mock transport for testing
        """
        self._config = config
        self._transport = transport
        self._lock = threading.Lock()

    @property
    def producer(self) -> Producer:
        """Lazy initialization of Kafka producer."""
        if self._producer is None:
            with self._lock:
                if self._producer is None:
                    if self._transport is not None:
                        self._producer = self._transport
                    else:
                        self._producer = Producer(self._config)
                        logger.info(
                            f"Kafka producer initialized for {self.__class__.__name__}, "
                            f"brokers: {self._config.get('bootstrap.servers')}"
                        )
        return self._producer

    def _delivery_callback(
        self,
        err: KafkaError | None,
        msg: KafkaMessage,
    ) -> None:
        """Called when message delivery is confirmed or fails."""
        if err is not None:
            logger.error(
                f"Message delivery failed: {err}",
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "error": str(err),
                },
            )
        else:
            logger.debug(
                f"Message delivered to {msg.topic()}[{msg.partition()}] "
                f"@ offset {msg.offset()} (leader: broker {msg.leader_epoch()})"
            )

    def publish(
        self,
        data: SchemaT,
        key: str | None = None,
        headers: dict[str, str] | None = None,
        flush: bool = False,
    ) -> None:
        """
        Publish a message to Kafka.

        Args:
            data: Validated Pydantic model instance
            key: Optional message key for partitioning (ensures ordering)
            headers: Optional message headers (metadata)
            flush: If True, wait for delivery confirmation

        Raises:
            KafkaPublisherException: If publishing fails
        """
        message = data.model_dump_json()

        # Prepare headers if provided
        kafka_headers: list[tuple[str, str | bytes | None]] | None = None
        if headers:
            kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

        try:
            self.producer.produce(
                topic=self.topic,
                value=message.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                headers=kafka_headers,
                callback=self._delivery_callback,
            )

            # Trigger delivery of buffered messages (non-blocking)
            self.producer.poll(0)

            if flush:
                self.flush()

        except KafkaException as e:
            logger.exception(f"Failed to publish to {self.topic}")
            raise KafkaPublisherException(f"Failed to publish message: {e}") from e
        except BufferError:
            # Local queue is full - wait and retry
            logger.warning("Producer buffer full, flushing...")
            self.flush(timeout=10.0)
            # Retry once after flush
            self.producer.produce(
                topic=self.topic,
                value=message.encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                headers=kafka_headers,
                callback=self._delivery_callback,
            )

    def flush(self, timeout: float = 10.0) -> int:
        """
        Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue (0 if all delivered)
        """
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.warning(
                f"{self.__class__.__name__}: {remaining} messages still in queue after {timeout}s flush timeout"
            )
        return remaining

    def is_initialized(self) -> bool:
        """Check if the producer has been initialized."""
        return self._producer is not None


# Registry of producers for cleanup
_producers: list[BaseKafkaProducer[Any]] = []
_producers_lock = threading.Lock()


def get_kafka_config() -> dict[str, Any]:
    """
    Get Kafka configuration from Django settings.

    Uses KAFKA_PRODUCER_CONFIG if available, otherwise builds
    minimal config from KAFKA_BOOTSTRAP_SERVERS.
    """
    # Try to use full producer config
    if hasattr(settings, "KAFKA_PRODUCER_CONFIG"):
        return dict(settings.KAFKA_PRODUCER_CONFIG)

    # Fallback to minimal config
    return {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "acks": "all",
        "retries": 3,
        "enable.idempotence": True,
    }


def create_producer(
    producer_class: type[BaseKafkaProducer[Any]],
    transport: Any = None,
) -> BaseKafkaProducer[Any]:
    """
    Create a producer instance.

    Args:
        producer_class: The producer class to instantiate
        transport: Optional mock transport for testing

    Returns:
        Configured producer instance
    """
    # Use mock in testing mode if available
    if transport is None:
        is_testing = getattr(settings, "IS_TESTING_MODE", False)
        if is_testing:
            # You can create a MockProducer class if needed
            pass

    config = get_kafka_config()
    instance = producer_class(config, transport=transport)

    with _producers_lock:
        _producers.append(instance)

    return instance


def flush_all_producers(timeout: float = 10.0) -> dict[str, int]:
    """
    Flush all registered producers.

    Returns:
        Dict mapping producer class name to number of undelivered messages
    """
    results = {}

    with _producers_lock:
        producers = list(_producers)

    for producer in producers:
        try:
            if producer.is_initialized():
                remaining = producer.flush(timeout)
                results[producer.__class__.__name__] = remaining
                if remaining > 0:
                    logger.warning(f"Kafka producer {producer.__class__.__name__}: {remaining} messages not delivered")
        except Exception:
            logger.exception(f"Error flushing Kafka producer {producer.__class__.__name__}")
            results[producer.__class__.__name__] = -1

    return results
