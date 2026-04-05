import logging

from prototype_highly_loaded_distributed_service_utils.kafka import (
    OTPNotificationSchema,
)

logger = logging.getLogger(__name__)


async def send_sms(message: OTPNotificationSchema) -> None:
    logger.info(f"Sending SMS to {message.phone} with secret code {message.secret_code}")
    # todo implement Turbosms or twillio


async def send_email(message: OTPNotificationSchema) -> None:
    logger.info(f"Sending Email to {message.email} with secret code {message.secret_code}")
    # TODO: Integrate with email service (SMTP, SendGrid, AWS SES, etc.)
