"""
Pydantic schemas for Kafka messages.

All message schemas should be defined here for type safety
and automatic validation before publishing to Kafka.

This is the single source of truth for all Kafka message schemas
across the microservices ecosystem.
"""

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationChannel(StrEnum):
    """Delivery channel for notifications."""

    SMS = "sms"
    EMAIL = "email"


class OTPNotificationSchema(BaseModel):
    """
    OTP notification message schema.

    This message is published to Kafka and consumed by the
    notification service to send OTP codes via SMS/Email.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "phone": "+380501234567",
                    "email": None,
                    "secret_code": "1234",
                    "verification_code": "123456",
                    "channel": "sms",
                    "expires_at": "2025-01-15T12:30:00Z",
                    "created_at": "2025-01-15T12:25:00Z",
                },
                {
                    "phone": None,
                    "email": "user@example.com",
                    "secret_code": "5678",
                    "verification_code": "654321",
                    "channel": "email",
                    "expires_at": "2025-01-15T12:30:00Z",
                    "created_at": "2025-01-15T12:25:00Z",
                },
            ]
        },
    )

    phone: str | None = Field(
        default=None,
        description="Phone number in E.164 format (e.g., +380501234567)",
        examples=["+380501234567", "+14155552671"],
    )
    email: str | None = Field(
        default=None,
        description="Email address for OTP delivery",
        examples=["user@example.com", "test@gmail.com"],
    )

    secret_code: str = Field(
        min_length=4,
        max_length=4,
        description="The OTP secret code to send (4 digits)",
        examples=["1234", "5678"],
    )
    verification_code: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit verification code for tracking",
        examples=["123456", "654321"],
    )

    channel: NotificationChannel = Field(
        default=NotificationChannel.SMS,
        description="Preferred delivery channel",
        examples=["sms", "email"],
    )
    expires_at: datetime = Field(
        description="When this OTP expires",
        examples=["2025-01-15T12:30:00"],
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this message was created",
        examples=["2025-01-15T12:25:00"],
    )

    @model_validator(mode="after")
    def validate_recipient(self) -> Self:
        """Validate that at least one of phone or email is provided."""
        if self.phone is None and self.email is None:
            raise ValueError("At least one of 'phone' or 'email' must be provided")
        return self
