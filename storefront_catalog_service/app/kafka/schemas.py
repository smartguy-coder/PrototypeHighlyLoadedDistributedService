"""
Pydantic schemas for Kafka messages.

All message schemas should be defined here for type safety
and automatic validation before publishing to Kafka.
"""

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationChannel(StrEnum):
    """Delivery channel for notifications."""

    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class OTPNotification(BaseModel):
    """
    OTP notification message schema.

    This message is published to Kafka and consumed by the
    notification service to send OTP codes via SMS/Email.
    """

    model_config = ConfigDict(extra="forbid")

    phone: str | None = Field(
        default=None,
        description="Phone number in E.164 format (e.g., +380501234567)",
    )
    email: str | None = Field(
        default=None,
        description="Email address for OTP delivery",
    )

    secret_code: str = Field(
        min_length=4,
        max_length=4,
        description="The OTP secret code to send (4 digits)",
    )
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit verification code for tracking",
    )

    channel: NotificationChannel = Field(
        default=NotificationChannel.SMS,
        description="Preferred delivery channel",
    )
    expires_at: datetime = Field(
        description="When this OTP expires",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this message was created",
    )

    @model_validator(mode="after")
    def validate_recipient(self) -> Self:
        """Validate that at least one of phone or email is provided."""
        if self.phone is None and self.email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided")
        return self
