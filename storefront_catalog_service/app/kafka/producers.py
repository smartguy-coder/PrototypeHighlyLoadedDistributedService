"""
Kafka producers for different domains.

Each producer is a singleton created at module load time.
Import and use directly:

    from kafka.producers import otp_notification_producer

    otp_notification_producer.publish({
        "phone": "+380501234567",
        "secret_code": "1234",
        ...
    })
"""

from kafka.producer import BaseKafkaProducer, create_producer
from kafka.schemas import OTPNotificationSchema
from kafka.topics import (
    TOPIC_NOTIFICATIONS_OTP,
)


class OTPNotificationProducer(BaseKafkaProducer[OTPNotificationSchema]):
    """Producer for OTP notification messages."""

    topic = TOPIC_NOTIFICATIONS_OTP
    schema = OTPNotificationSchema


# Create singleton instances
# These are lazily initialized - Kafka connection is not made until first publish
otp_notification_producer = create_producer(OTPNotificationProducer)
