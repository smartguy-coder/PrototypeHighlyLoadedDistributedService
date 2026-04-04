"""
Kafka schemas and topics for microservices communication.

This module provides shared Pydantic schemas and topic names for Kafka messages,
ensuring type safety and consistency across all services.

Usage in Django (storefront_catalog_service):
    from prototype_highly_loaded_distributed_service_utils.kafka import (
        OTPNotificationSchema,
        KafkaTopic,
    )

    producer.publish(topic=KafkaTopic.NOTIFICATIONS_OTP, ...)

Usage in FastStream:
    from prototype_highly_loaded_distributed_service_utils.kafka import (
        OTPNotificationSchema,
        KafkaTopic,
    )

    @broker.subscriber(KafkaTopic.NOTIFICATIONS_OTP)
    async def handle_otp(message: OTPNotificationSchema):
        ...
"""

from prototype_highly_loaded_distributed_service_utils.kafka.schemas import (
    NotificationChannel,
    OTPNotificationSchema,
)
from prototype_highly_loaded_distributed_service_utils.kafka.topics import (
    KafkaTopic,
)

__all__ = [
    # Schemas
    "NotificationChannel",
    "OTPNotificationSchema",
    # Topics
    "KafkaTopic",
]
