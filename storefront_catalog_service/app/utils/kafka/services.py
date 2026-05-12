"""
Kafka notification services.

High-level functions for publishing notifications via Kafka.
These are the entry points for other parts of the application
to send notifications without knowing Kafka internals.

All functions accept only primitives — no Django request objects.
"""

import logging
from datetime import datetime

from prototype_highly_loaded_distributed_service_utils.kafka import (
    NotificationChannel,
    OTPNotificationSchema,
)
from utils.kafka.producer import KafkaPublisherException
from utils.kafka.producers import otp_notification_producer

logger = logging.getLogger(__name__)


def send_otp_notification(
    verification_code: str,
    secret_code: str,
    expires_at: datetime,
    email: str | None = None,
    phone: str | None = None,
) -> bool:
    """
    Send OTP notification via Kafka to the notification service.

    Args:
        verification_code: 6-digit verification code
        secret_code: 4-digit secret code to send to user
        expires_at: When the OTP expires
        email: Email address (if sending via email)
        phone: Phone number in E.164 format (if sending via SMS)

    Returns:
        True if message was published successfully, False otherwise
    """
    if not email and not phone:
        logger.error("send_otp_notification: either email or phone is required")
        return False

    # Determine delivery channel
    channel = NotificationChannel.EMAIL if email else NotificationChannel.SMS
    target = email or phone

    # Build notification payload
    notification = OTPNotificationSchema(
        email=email,
        phone=phone,
        secret_code=secret_code,
        verification_code=verification_code,
        channel=channel,
        expires_at=expires_at,
    )

    try:
        otp_notification_producer.publish(
            data=notification,
            key=target,
            headers={
                "source": "storefront-catalog-service",
                "event_type": "otp.created",
            },
            flush=True,  # Ensure message is delivered before returning
        )
        logger.info(f"OTP notification published to Kafka for {target}")
        return True

    except KafkaPublisherException:
        logger.exception(f"Failed to publish OTP notification for {target}")
        return False
