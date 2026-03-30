"""
Kafka settings for the storefront catalog service.

This configuration supports multi-broker Kafka clusters running in KRaft mode
(without Zookeeper).

Environment variables:
    KAFKA_BOOTSTRAP_SERVERS: Comma-separated list of broker addresses
                             Default: "kafka-1:9092,kafka-2:9092,kafka-3:9092"

For local development with docker-compose:
    - Internal (container-to-container): kafka-1:9092,kafka-2:9092,kafka-3:9092
    - External (host machine): localhost:29092,localhost:29093,localhost:29094
"""

from decouple import config

# Kafka cluster bootstrap servers
# Multiple brokers for high availability - if one fails, others take over
KAFKA_BOOTSTRAP_SERVERS = config("KAFKA_BOOTSTRAP_SERVERS", default="kafka-1:9092,kafka-2:9092,kafka-3:9092")

# Producer settings (production-like)
KAFKA_PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    # Durability: wait for all in-sync replicas to acknowledge
    "acks": "all",
    # Retry on transient failures
    "retries": 3,
    "retry.backoff.ms": 100,
    # Batching for throughput
    "linger.ms": 5,
    "batch.size": 16384,
    # Compression
    "compression.type": "lz4",
    # Idempotence: exactly-once semantics within a partition
    "enable.idempotence": True,
    # Request timeout
    "request.timeout.ms": 30000,
    "delivery.timeout.ms": 120000,
}

# Consumer settings (for future use)
KAFKA_CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    # Consumer group
    "group.id": "storefront-catalog-service",
    # Start from earliest message if no offset exists
    "auto.offset.reset": "earliest",
    # Manual commit for at-least-once semantics
    "enable.auto.commit": False,
    # Heartbeat and session timeout
    "heartbeat.interval.ms": 3000,
    "session.timeout.ms": 30000,
    # Fetch settings
    "fetch.min.bytes": 1,
    "fetch.max.wait.ms": 500,
}
