# FastStream

FastStream is a powerful Python framework for building asynchronous message consumers with support for Kafka, RabbitMQ, NATS, and Redis Streams.

---

## Table of Contents

1. [Theory](#theory)
2. [Why FastStream](#why-faststream)
3. [Architecture](#architecture)
4. [Key Concepts](#key-concepts)
5. [Installation](#installation)
6. [Our Implementation](#our-implementation)
7. [Lifespan Context Manager](#lifespan-context-manager)
8. [ASGI & AsyncAPI Documentation](#asgi-asyncapi-documentation)
9. [Message Handling](#message-handling)
10. [Configuration](#configuration)
11. [Docker Setup](#docker-setup)
12. [Testing](#testing)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

---

## Theory

### What is FastStream?

FastStream is a **modern Python framework** for building asynchronous message-driven applications. Think of it as "FastAPI for message brokers" — it brings the same developer experience (type hints, dependency injection, automatic documentation) to event streaming.

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastStream Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Message Broker                FastStream App                  │
│   ┌──────────────┐             ┌──────────────────────────────┐ │
│   │              │             │                              │ │
│   │    Kafka     │──messages──►│  @broker.subscriber(topic)   │ │
│   │   RabbitMQ   │             │  async def handler(msg):     │ │
│   │    NATS      │◄──publish───│      # process message       │ │
│   │    Redis     │             │      return response         │ │
│   │              │             │                              │ │
│   └──────────────┘             └──────────────────────────────┘ │
│                                                                 │
│   Key Features:                                                 │
│   • Async/await native                                          │
│   • Type-safe message validation (Pydantic)                     │
│   • Dependency injection (like FastAPI)                         │
│   • Automatic AsyncAPI documentation                            │
│   • Built-in testing utilities                                  │
│   • ASGI support for health checks                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why FastStream

### Comparison with Alternatives

| Feature | FastStream | confluent-kafka | aiokafka | Faust |
|---------|------------|-----------------|----------|-------|
| **Async native** | ✅ Yes | ❌ No (callbacks) | ✅ Yes | ✅ Yes |
| **Type validation** | ✅ Pydantic | ❌ Manual | ❌ Manual | ⚠️ Limited |
| **Dependency injection** | ✅ Built-in | ❌ No | ❌ No | ❌ No |
| **Multi-broker** | ✅ Kafka, RabbitMQ, NATS, Redis | ❌ Kafka only | ❌ Kafka only | ❌ Kafka only |
| **Testing utilities** | ✅ TestClient | ❌ No | ❌ No | ⚠️ Limited |
| **AsyncAPI docs** | ✅ Auto-generated | ❌ No | ❌ No | ❌ No |
| **Learning curve** | Low (FastAPI-like) | High | Medium | High |

---

## Architecture

### Project Structure (Our Implementation)

```
notification_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastStream app entry point
│   ├── config.py            # Pydantic settings
│   └── handlers/
│       ├── __init__.py
│       └── otp.py           # OTP notification handler
├── pyproject.toml
├── Dockerfile
└── README.md
```

---

## Key Concepts

### 1. Broker

The broker is the connection to your message system:

```python
from faststream.kafka import KafkaBroker

broker = KafkaBroker(["kafka-1:9092", "kafka-2:9092", "kafka-3:9092"])
```

### 2. Router

Routers group related subscribers (like FastAPI routers):

```python
from faststream.kafka import KafkaRouter

router = KafkaRouter()

@router.subscriber("my-topic", group_id="my-group")
async def handle(msg: dict) -> None:
    print(msg)

# Include in broker
broker.include_router(router)
```

### 3. Subscriber (Consumer)

Subscribers handle incoming messages with automatic Pydantic validation:

```python
from pydantic import BaseModel

class OTPNotification(BaseModel):
    phone: str
    code: str

@router.subscriber("notifications.otp", group_id="notification-group")
async def handle_otp(msg: OTPNotification) -> None:
    print(f"Sending OTP {msg.code} to {msg.phone}")
```

### 4. Application

The app ties everything together:

```python
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker(["kafka-1:9092"])
app = FastStream(broker)
```

---

## Installation

```bash
# With Kafka support
pip install "faststream[kafka]"

# With CLI tools
pip install "faststream[kafka,cli]"

# With ASGI server for docs
pip install "faststream[kafka,cli]" uvicorn
```

### pyproject.toml

```toml
[project]
dependencies = [
    "faststream[kafka,cli]>=0.6.7",
    "pydantic-settings>=2.0.0",
    "uvicorn>=0.30.0",
]
```

---

## Our Implementation

### main.py

```python
"""
FastStream Kafka consumer for Notification Service.

Usage:
    # Development (with auto-reload):
    faststream run app.main:app --reload

    # Production (ASGI with docs):
    uvicorn app.main:asgi_app --host 0.0.0.0 --port 11111
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from faststream import ContextRepo, FastStream
from faststream.asgi import AsgiFastStream, make_ping_asgi
from faststream.kafka import KafkaBroker

from config import settings
from handlers import otp_router

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_broker() -> KafkaBroker:
    """Create and configure the Kafka broker."""
    broker = KafkaBroker(settings.kafka_bootstrap_servers_list)
    broker.include_router(otp_router)
    return broker


@asynccontextmanager
async def lifespan(context: ContextRepo) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    # === STARTUP ===
    logger.info(f"Starting {settings.service_name}...")
    logger.info(f"Connecting to Kafka: {settings.kafka_bootstrap_servers}")
    logger.info(f"Consumer group: {settings.kafka_consumer_group}")

    # Set global context (accessible in handlers via Context())
    context.set_global("settings", settings)
    context.set_global("logger", logger)

    logger.info(f"{settings.service_name} started successfully")

    yield

    # === SHUTDOWN ===
    logger.info(f"Shutting down {settings.service_name}...")
    logger.info(f"{settings.service_name} shutdown complete")


def create_app() -> FastStream:
    """Create standard FastStream app."""
    broker = create_broker()
    return FastStream(broker, lifespan=lifespan)


def create_asgi_app() -> AsgiFastStream:
    """Create ASGI app with AsyncAPI documentation."""
    broker = create_broker()

    return AsgiFastStream(
        broker,
        asgi_routes=[
            ("/health", make_ping_asgi(broker, timeout=5.0)),
        ],
        asyncapi_path="/docs",
        lifespan=lifespan,
    )


# Standard FastStream app
app = create_app()

# ASGI app with docs
asgi_app = create_asgi_app()
```

### handlers/otp.py

```python
"""OTP notification handler."""

import logging

from faststream.kafka import KafkaRouter

from config import settings
from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    NotificationChannel,
    OTPNotificationSchema,
)

logger = logging.getLogger(__name__)
router = KafkaRouter()


@router.subscriber(
    KafkaTopic.NOTIFICATIONS_OTP,
    group_id=settings.kafka_consumer_group,
    auto_offset_reset=settings.kafka_auto_offset_reset,
)
async def handle_otp_notification(message: OTPNotificationSchema) -> None:
    """Handle incoming OTP notification."""
    logger.info(
        f"Received OTP notification: "
        f"verification_code={message.verification_code}, "
        f"channel={message.channel}"
    )

    if message.channel == NotificationChannel.SMS:
        await send_sms(message)
    else:
        await send_email(message)

    logger.info(f"Successfully processed OTP: {message.verification_code}")


async def send_sms(message: OTPNotificationSchema) -> None:
    logger.info(f"Sending SMS to {message.phone}")
    # TODO: Implement Twilio/TurboSMS


async def send_email(message: OTPNotificationSchema) -> None:
    logger.info(f"Sending Email to {message.email}")
    # TODO: Implement SMTP/SendGrid/AWS SES
```

---

## Lifespan Context Manager

FastStream supports lifespan context managers for startup/shutdown logic:

```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from faststream import ContextRepo

@asynccontextmanager
async def lifespan(context: ContextRepo) -> AsyncIterator[None]:
    """
    Lifespan context manager.

    - Code BEFORE yield: runs on startup (before broker connects)
    - Code AFTER yield: runs on shutdown (after broker disconnects)
    """
    # === STARTUP ===
    logger.info("Starting service...")

    # Initialize resources
    db = await Database.connect()
    redis = await Redis.connect()

    # Store in global context (accessible via Context() in handlers)
    context.set_global("db", db)
    context.set_global("redis", redis)

    yield

    # === SHUTDOWN ===
    logger.info("Shutting down...")

    # Cleanup resources
    await redis.close()
    await db.disconnect()


# Pass to FastStream
app = FastStream(broker, lifespan=lifespan)
```

### Accessing Context in Handlers

```python
from faststream import Context

@router.subscriber("my-topic")
async def handler(
    msg: dict,
    db: Database = Context(),      # Injected from lifespan
    settings: Settings = Context(), # Injected from lifespan
) -> None:
    await db.insert(msg)
```

---

## ASGI & AsyncAPI Documentation

FastStream provides built-in ASGI support for serving AsyncAPI documentation and health checks.

### AsgiFastStream

```python
from faststream.asgi import AsgiFastStream, make_ping_asgi

asgi_app = AsgiFastStream(
    broker,
    asgi_routes=[
        ("/health", make_ping_asgi(broker, timeout=5.0)),
    ],
    asyncapi_path="/docs",
    lifespan=lifespan,
)
```

### Available Endpoints

| Endpoint | Description |
|----------|-------------|
| `/docs` | AsyncAPI documentation (interactive UI) |
| `/health` | Health check (returns 200 if broker connected) |

### Running with Uvicorn

```bash
# Development (with auto-reload)
uvicorn main:asgi_app --host 0.0.0.0 --port 11111 --reload

# Production
uvicorn main:asgi_app --host 0.0.0.0 --port 11111 --workers 4
```

### AsyncAPI Documentation

AsyncAPI is the async equivalent of OpenAPI/Swagger. It documents:

- **Channels (Topics)** — Kafka topics your service subscribes to
- **Message Schemas** — Pydantic models for message validation
- **Servers** — Kafka broker connections

```
┌─────────────────────────────────────────────────────────────────┐
│                    AsyncAPI Documentation                       │
│                    http://localhost:11111/docs                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📨 Channels                                                    │
│     └─ notifications.otp                                        │
│        └─ subscribe: OTPNotificationSchema                      │
│                                                                 │
│  📦 Message Schemas                                             │
│     └─ OTPNotificationSchema                                    │
│        ├─ phone: string | null                                  │
│        ├─ email: string | null                                  │
│        ├─ secret_code: string                                   │
│        ├─ verification_code: string                             │
│        ├─ channel: NotificationChannel                          │
│        └─ expires_at: datetime                                  │
│                                                                 │
│  🔗 Servers                                                     │
│     └─ kafka-1:9092, kafka-2:9092, kafka-3:9092                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Message Handling

### Accessing Raw Message

```python
from faststream.kafka import KafkaMessage

@router.subscriber("my-topic")
async def handler(
    body: dict,
    msg: KafkaMessage,  # Raw Kafka message
) -> None:
    print(f"Topic: {msg.topic}")
    print(f"Partition: {msg.partition}")
    print(f"Offset: {msg.offset}")
    print(f"Key: {msg.key}")
    print(f"Headers: {msg.headers}")
```

### Consumer Groups

```python
@router.subscriber(
    "notifications.otp",
    group_id="notification-service-group",  # Consumer group
    auto_offset_reset="earliest",            # Start from beginning
)
async def handle_otp(msg: dict) -> None:
    pass
```

### Error Handling

```python
from faststream.exceptions import AckMessage, NackMessage, RejectMessage

@router.subscriber("my-topic")
async def handler(msg: dict) -> None:
    try:
        await process(msg)
    except TemporaryError:
        raise NackMessage()     # Requeue for retry
    except PermanentError:
        raise RejectMessage()   # Send to DLQ
    except Exception:
        raise AckMessage()      # Acknowledge despite error
```

---

## Configuration

### config.py

```python
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service identification
    service_name: str = "notification-service"
    log_level: str = "INFO"

    # Kafka connection
    kafka_bootstrap_servers: str = "kafka-1:9092,kafka-2:9092,kafka-3:9092"

    # Kafka consumer settings
    kafka_consumer_group: str = "notification-service-group"
    kafka_auto_offset_reset: str = "earliest"

    @property
    def kafka_bootstrap_servers_list(self) -> list[str]:
        """Return bootstrap servers as a list."""
        return [s.strip() for s in self.kafka_bootstrap_servers.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
```

### Environment Variables

```bash
# .env
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9092,kafka-3:9092
KAFKA_CONSUMER_GROUP=notification-service-group
LOG_LEVEL=INFO
```

---

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

COPY pyproject.toml uv.lock /app/
RUN uv pip install --system --no-cache .

COPY /app /app

EXPOSE 11111

# Run ASGI app with AsyncAPI docs
CMD ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "11111"]
```

### docker-compose.yml

```yaml
notification_service:
  container_name: notification_service
  hostname: notificationService
  build:
    dockerfile: Dockerfile
    context: ./notification_service
  restart: unless-stopped
  ports:
    - "11111:11111"
  depends_on:
    kafka-1:
      condition: service_healthy
    kafka-2:
      condition: service_healthy
    kafka-3:
      condition: service_healthy
  # Development with auto-reload
  command: ["uvicorn", "main:asgi_app", "--host", "0.0.0.0", "--port", "11111", "--reload"]
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:11111/health"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 10s
  volumes:
    - ./notification_service/app:/app
  env_file:
    - .env
```

### Available Endpoints

| URL | Description |
|-----|-------------|
| http://localhost:11111/docs | AsyncAPI documentation |
| http://localhost:11111/health | Health check endpoint |

---

## Testing

FastStream provides excellent testing utilities:

### Unit Testing with TestKafkaBroker

```python
import pytest
from faststream.kafka import TestKafkaBroker

from app.main import broker
from app.handlers.otp import handle_otp_notification


@pytest.mark.asyncio
async def test_otp_handler():
    async with TestKafkaBroker(broker) as br:
        await br.publish(
            {
                "phone": "+380501234567",
                "secret_code": "1234",
                "verification_code": "123456",
                "channel": "sms",
                "expires_at": "2024-01-01T12:00:00Z",
            },
            topic="notifications.otp",
        )

        # Assert handler was called
        handle_otp_notification.mock.assert_called_once()
```

### Mocking Dependencies

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mocked_sms():
    mock_sms = AsyncMock()

    async with TestKafkaBroker(broker) as br:
        # Inject mock
        br.dependency_overrides[send_sms] = mock_sms

        await br.publish({"phone": "+380...", ...}, topic="notifications.otp")

        mock_sms.assert_called_once()
```

---

## Best Practices

### 1. Use Routers for Organization

```python
# handlers/otp.py
router = KafkaRouter()

@router.subscriber("notifications.otp", ...)
async def handle_otp(...): ...

# handlers/email.py
router = KafkaRouter()

@router.subscriber("notifications.email", ...)
async def handle_email(...): ...

# main.py
broker.include_router(otp_router)
broker.include_router(email_router)
```

### 2. Idempotent Handlers

```python
@router.subscriber("orders.created")
async def handle_order(
    order: dict,
    msg: KafkaMessage,
    db: Database = Context(),
) -> None:
    # Idempotency key from message
    idempotency_key = f"{msg.topic}-{msg.partition}-{msg.offset}"

    if await db.exists("processed", idempotency_key):
        return  # Already processed

    await process_order(order)
    await db.insert("processed", {"id": idempotency_key})
```

### 3. Graceful Shutdown

Lifespan context manager ensures graceful shutdown:

```python
@asynccontextmanager
async def lifespan(context: ContextRepo) -> AsyncIterator[None]:
    # Startup
    http_client = httpx.AsyncClient()
    context.set_global("http", http_client)

    yield

    # Shutdown - cleanup resources
    await http_client.aclose()
```

### 4. Structured Logging

```python
import logging

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

@router.subscriber("my-topic")
async def handler(msg: dict) -> None:
    logger.info(f"Processing message", extra={"msg_id": msg.get("id")})
```

---

## Troubleshooting

### Common Issues

#### 1. "No brokers available"

```bash
# Verify Kafka is running
docker compose ps kafka-1 kafka-2 kafka-3

# Check logs
docker compose logs notification_service
```

#### 2. "Message validation failed"

```python
# Accept dict first, then validate manually
@router.subscriber("my-topic")
async def handler(msg: dict) -> None:
    try:
        validated = MySchema.model_validate(msg)
    except ValidationError as e:
        logger.error(f"Invalid message: {e}")
        raise RejectMessage()
```

#### 3. Consumer lag growing

```bash
# Check consumer group status
docker compose exec kafka-1 kafka-consumer-groups \
    --bootstrap-server kafka-1:9092 \
    --describe \
    --group notification-service-group
```

#### 4. Health check failing

```bash
# Test health endpoint manually
curl http://localhost:11111/health

# Check if broker is connected
docker compose logs notification_service | grep "started successfully"
```

---

## Further Reading

- [FastStream Documentation](https://faststream.airt.ai/)
- [FastStream GitHub](https://github.com/airtai/faststream)
- [AsyncAPI Specification](https://www.asyncapi.com/)
- [Apache Kafka](kafka.md)

---

## Related Documentation

- [Technologies Overview](index.md)
- [Apache Kafka](kafka.md)
- [Architecture Diagrams](../about/diagrams.md)
