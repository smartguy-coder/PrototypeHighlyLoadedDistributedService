"""
Kafka module.

Provides Kafka producers, schemas, and high-level services
for async messaging.

Quick Start (recommended - use services):
    from kafka.services import send_otp_notification

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
"""

from kafka.producer import (
    BaseKafkaProducer,
    KafkaPublisherException,
    create_producer,
    flush_all_producers,
)
from kafka.producers import (
    otp_notification_producer,
)
from kafka.schemas import (
    NotificationChannel,
    OTPNotificationSchema,
)
from kafka.services import (
    send_otp_notification,
)
from kafka.topics import (
    TOPIC_NOTIFICATIONS_OTP,
)

__all__ = [
    "TOPIC_NOTIFICATIONS_OTP",
    "BaseKafkaProducer",
    "KafkaPublisherException",
    "NotificationChannel",
    "OTPNotificationSchema",
    "create_producer",
    "flush_all_producers",
    "otp_notification_producer",
    "send_otp_notification",
]
