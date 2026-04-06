"""
FastStream Kafka consumer for Notification Service.

This is the main entry point for the notification service.
It creates a FastStream application with a Kafka broker and
includes all message handlers.

Usage:
    # Development (with auto-reload):
    faststream run app.main:app --reload

    # Production (ASGI with docs):
    uvicorn app.main:asgi_app --host 0.0.0.0 --port 11111

    # Or via FastStream CLI:
    faststream run app.main:asgi_app --host 0.0.0.0 --port 11111
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from config import settings
from faststream import ContextRepo, FastStream
from faststream.asgi import AsgiFastStream, make_ping_asgi
from faststream.kafka import KafkaBroker
from handlers import otp_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
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
    logger.info(f"Starting {settings.SERVICE_NAME}...")
    logger.info(f"Connecting to Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Consumer group: {settings.KAFKA_CONSUMER_GROUP}")

    # Set global context (accessible in handlers via Context())
    context.set_global("settings", settings)

    logger.info(f"{settings.SERVICE_NAME} started successfully")

    yield

    logger.info(f"Shutting down {settings.SERVICE_NAME}...")
    logger.info(f"{settings.SERVICE_NAME} shutdown complete")


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
        asyncapi_path="/",
        lifespan=lifespan,
    )


# Standard FastStream app
app = create_app()

# ASGI app with docs
asgi_app = create_asgi_app()
