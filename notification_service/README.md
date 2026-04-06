# Notification Service

FastStream-based Kafka consumer service for handling notifications (SMS, Email).

## Architecture

This service consumes messages from Kafka topics and dispatches them to the appropriate notification channel:

```
┌─────────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Storefront Service │──►   │      Kafka      │  ──► │ Notification    │
│  (Producer)         │      │  notifications. │      │ Service         │
└─────────────────────┘      │  otp            │      │ (Consumer)      │
                             └─────────────────┘      └────────┬────────┘
                                                               │
                                                    ┌──────────┴──────────┐
                                                    │                     │
                                               ┌────▼────┐          ┌─────▼────┐
                                               │   SMS   │          │  Email   │
                                               │ Provider│          │ Provider │
                                               └─────────┘          └──────────┘
```

## Topics

| Topic              | Schema                  | Description                    |
|--------------------|-------------------------|--------------------------------|
| `notifications.otp`| `OTPNotificationSchema` | OTP codes for verification     |

## Running

### With Docker Compose (recommended)

```bash
# From the project root
docker-compose up notification_service
```

### Local Development

```bash
cd notification_service

# Install dependencies
uv sync

# Run with auto-reload (from app/ directory)
cd app
uv run faststream run main:app --reload
```

## Configuration

Environment variables (from `.env`):

| Variable                  | Default                                   | Description                    |
|---------------------------|-------------------------------------------|--------------------------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka-1:9092,kafka-2:9092,kafka-3:9092`  | Kafka cluster addresses        |
| `LOG_LEVEL`               | `INFO`                                    | Logging level                  |

## Message Schema

### OTP Notification

```json
{
  "phone": "+380501234567",
  "email": "user@example.com",
  "secret_code": "1234",
  "verification_code": "123456",
  "channel": "sms",
  "expires_at": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T11:55:00Z"
}
```

## Project Structure

```
notification_service/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings from environment
│   ├── main.py            # FastStream application
│   └── handlers/
│       ├── __init__.py
│       └── otp.py         # OTP notification handler
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Testing

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy app

# Linting
uv run ruff check app
```

## Adding New Handlers

1. Create a new handler file in `app/handlers/`
2. Define a router with subscribers
3. Import and include the router in `app/handlers/__init__.py`
4. Add the topic to the shared utils package

Example:

```python
# app/handlers/order.py
from faststream.kafka import KafkaRouter
from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    OrderNotificationSchema,
)

router = KafkaRouter()

@router.subscriber(KafkaTopic.ORDERS_CREATED)
async def handle_order_created(message: OrderNotificationSchema) -> None:
    # Process order notification
    ...
```
