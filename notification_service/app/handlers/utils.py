"""
OTP delivery helpers.

All log records emitted from this module follow the ClickHouse schema used by
the Vector pipeline:

  - `log_type` selects the TTL bucket: 'audit' (60d) for delivery attempts,
    'error' (30d) for failures, 'app' (14d, default) for everything else.
  - `extra` carries arbitrary JSON context that survives end-to-end into the
    `extra` column in ClickHouse and is queryable via JSONExtract* in Grafana.

NOTE on PII: never put `secret_code` (the OTP itself) into log fields.
Use `verification_code` — it is the public tracking id and safe to store.
"""

import json
import logging

from prototype_highly_loaded_distributed_service_utils.kafka import (
    OTPNotificationSchema,
)

logger = logging.getLogger(__name__)


async def send_sms(message: OTPNotificationSchema) -> None:
    logger.info(
        "Dispatching OTP via SMS",
        extra={
            "log_type": "audit",
            "extra": json.dumps(
                {
                    "phone": message.phone,
                    "verification_code": message.verification_code,
                    "channel": "sms",
                    "expires_at": message.expires_at.isoformat(),
                }
            ),
        },
    )

    # TODO: integrate with Turbosms / Twilio.
    # Until a provider is wired in, surface the gap as a warning so it lands
    # in the `error` TTL bucket and shows up on the failures dashboard.
    logger.warning(
        "SMS provider not configured — OTP not delivered",
        extra={
            "log_type": "error",
            "extra": json.dumps(
                {
                    "phone": message.phone,
                    "verification_code": message.verification_code,
                    "reason": "provider_not_configured",
                }
            ),
        },
    )


async def send_email(message: OTPNotificationSchema) -> None:
    logger.info(
        "Dispatching OTP via Email",
        extra={
            "log_type": "audit",
            "extra": json.dumps(
                {
                    "email": message.email,
                    "verification_code": message.verification_code,
                    "channel": "email",
                    "expires_at": message.expires_at.isoformat(),
                }
            ),
        },
    )

    # TODO: Integrate with email service (SMTP, SendGrid, AWS SES, etc.)
    logger.warning(
        "Email provider not configured — OTP not delivered",
        extra={
            "log_type": "error",
            "extra": json.dumps(
                {
                    "email": message.email,
                    "verification_code": message.verification_code,
                    "reason": "provider_not_configured",
                }
            ),
        },
    )
