"""
Kafka module.

Provides Kafka producers, schemas, and high-level services
for async messaging.

Quick Start (recommended - use services):
    from utils.kafka.services import send_otp_notification

    send_otp_notification(
        verification_code="123456",
        secret_code="1234",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        phone="+380501234567",
    )

Low-level access (for custom use cases):
    from kafka.producers import otp_notification_producer

    otp_notification_producer.publish({
        "phone": "+380501234567",
        "secret_code": "1234",
        ...
    })

Schemas and topics (from shared utils package):
    from prototype_highly_loaded_distributed_service_utils.kafka import (
        NotificationChannel,
        OTPNotificationSchema,
        KafkaTopic,
    )
"""

# Re-export schemas and topics from shared package for convenience
from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    NotificationChannel,
    OTPNotificationSchema,
)
from utils.kafka.producer import (
    BaseKafkaProducer,
    KafkaPublisherException,
    create_producer,
    flush_all_producers,
)
from utils.kafka.producers import (
    otp_notification_producer,
)
from utils.kafka.services import (
    send_otp_notification,
)

__all__ = [
    "BaseKafkaProducer",
    "KafkaPublisherException",
    "KafkaTopic",
    "NotificationChannel",
    "OTPNotificationSchema",
    "create_producer",
    "flush_all_producers",
    "otp_notification_producer",
    "send_otp_notification",
]
