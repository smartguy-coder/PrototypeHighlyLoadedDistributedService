"""
OTP notification handler.

Handles incoming OTP notification messages from Kafka
and dispatches them to the appropriate delivery channel.
"""

import logging

from config import settings
from faststream.kafka import KafkaRouter
from handlers.utils import send_email, send_sms
from prototype_highly_loaded_distributed_service_utils.kafka import (
    KafkaTopic,
    NotificationChannel,
    OTPNotificationSchema,
)

logger = logging.getLogger(__name__)

router = KafkaRouter()


@router.subscriber(
    KafkaTopic.NOTIFICATIONS_OTP,
    group_id=settings.KAFKA_CONSUMER_GROUP,
    auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
)
async def handle_otp_notification(message: OTPNotificationSchema) -> None:
    logger.info(
        f"Received OTP notification: "
        f"verification_code={message.verification_code}, "
        f"channel={message.channel}, "
        f"expires_at={message.expires_at}"
    )

    try:
        if message.channel == NotificationChannel.SMS:
            await send_sms(message)
        else:
            await send_email(message)

        logger.info(f"Successfully processed OTP notification: verification_code={message.verification_code}")
    except Exception as e:
        logger.exception(
            f"Failed to process OTP notification: verification_code={message.verification_code}, error={e}"
        )
        raise
