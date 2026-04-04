"""Tests for Kafka schemas."""

from datetime import datetime, timedelta
from enum import StrEnum

import pytest
from pydantic import ValidationError

from prototype_highly_loaded_distributed_service_utils.kafka import (
    NotificationChannel,
    OTPNotificationSchema,
)


class TestNotificationChannel:
    """Tests for NotificationChannel enum."""

    def test_is_str_enum(self) -> None:
        """NotificationChannel should be a StrEnum."""
        assert issubclass(NotificationChannel, StrEnum)

    def test_sms_value(self) -> None:
        """SMS channel should have correct value."""
        assert NotificationChannel.SMS == "sms"
        assert NotificationChannel.SMS.value == "sms"

    def test_email_value(self) -> None:
        """EMAIL channel should have correct value."""
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.EMAIL.value == "email"

    def test_all_channels(self) -> None:
        """Should have exactly 2 channels."""
        channels = list(NotificationChannel)
        assert len(channels) == 2
        assert NotificationChannel.SMS in channels
        assert NotificationChannel.EMAIL in channels


class TestOTPNotificationSchema:
    """Tests for OTPNotificationSchema."""

    @pytest.fixture
    def valid_phone_data(self) -> dict:
        """Valid data for phone notification."""
        return {
            "phone": "+380501234567",
            "secret_code": "1234",
            "verification_code": "123456",
            "expires_at": datetime.now() + timedelta(minutes=5),
        }

    @pytest.fixture
    def valid_email_data(self) -> dict:
        """Valid data for email notification."""
        return {
            "email": "test@example.com",
            "secret_code": "1234",
            "verification_code": "123456",
            "channel": NotificationChannel.EMAIL,
            "expires_at": datetime.now() + timedelta(minutes=5),
        }

    def test_create_with_phone(self, valid_phone_data: dict) -> None:
        """Should create schema with phone."""
        schema = OTPNotificationSchema(**valid_phone_data)
        assert schema.phone == "+380501234567"
        assert schema.email is None
        assert schema.secret_code == "1234"
        assert schema.verification_code == "123456"
        assert schema.channel == NotificationChannel.SMS

    def test_create_with_email(self, valid_email_data: dict) -> None:
        """Should create schema with email."""
        schema = OTPNotificationSchema(**valid_email_data)
        assert schema.email == "test@example.com"
        assert schema.phone is None
        assert schema.channel == NotificationChannel.EMAIL

    def test_create_with_both_phone_and_email(self, valid_phone_data: dict) -> None:
        """Should allow both phone and email."""
        valid_phone_data["email"] = "test@example.com"
        schema = OTPNotificationSchema(**valid_phone_data)
        assert schema.phone == "+380501234567"
        assert schema.email == "test@example.com"

    def test_requires_phone_or_email(self) -> None:
        """Should require at least phone or email."""
        with pytest.raises(ValidationError) as exc_info:
            OTPNotificationSchema(
                secret_code="1234",
                verification_code="123456",
                expires_at=datetime.now() + timedelta(minutes=5),
            )
        assert "At least one of 'phone' or 'email' must be provided" in str(exc_info.value)

    def test_secret_code_length_validation(self, valid_phone_data: dict) -> None:
        """Secret code must be exactly 4 characters."""
        # Too short
        valid_phone_data["secret_code"] = "123"
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

        # Too long
        valid_phone_data["secret_code"] = "12345"
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

        # Correct length
        valid_phone_data["secret_code"] = "1234"
        schema = OTPNotificationSchema(**valid_phone_data)
        assert schema.secret_code == "1234"

    def test_verification_code_length_validation(self, valid_phone_data: dict) -> None:
        """Verification code must be exactly 6 characters."""
        # Too short
        valid_phone_data["verification_code"] = "12345"
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

        # Too long
        valid_phone_data["verification_code"] = "1234567"
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

        # Correct length
        valid_phone_data["verification_code"] = "123456"
        schema = OTPNotificationSchema(**valid_phone_data)
        assert schema.verification_code == "123456"

    def test_default_channel_is_sms(self, valid_phone_data: dict) -> None:
        """Default channel should be SMS."""
        schema = OTPNotificationSchema(**valid_phone_data)
        assert schema.channel == NotificationChannel.SMS

    def test_created_at_default(self, valid_phone_data: dict) -> None:
        """created_at should have a default value."""
        before = datetime.now()
        schema = OTPNotificationSchema(**valid_phone_data)
        after = datetime.now()
        assert before <= schema.created_at <= after

    def test_expires_at_required(self, valid_phone_data: dict) -> None:
        """expires_at should be required."""
        del valid_phone_data["expires_at"]
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

    def test_extra_fields_forbidden(self, valid_phone_data: dict) -> None:
        """Extra fields should be forbidden."""
        valid_phone_data["extra_field"] = "not allowed"
        with pytest.raises(ValidationError):
            OTPNotificationSchema(**valid_phone_data)

    def test_json_serialization(self, valid_phone_data: dict) -> None:
        """Should serialize to JSON."""
        schema = OTPNotificationSchema(**valid_phone_data)
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "+380501234567" in json_str
        assert "1234" in json_str

    def test_dict_serialization(self, valid_phone_data: dict) -> None:
        """Should serialize to dict."""
        schema = OTPNotificationSchema(**valid_phone_data)
        data = schema.model_dump()
        assert isinstance(data, dict)
        assert data["phone"] == "+380501234567"
        assert data["secret_code"] == "1234"
        assert data["channel"] == "sms"

    def test_model_from_json(self, valid_phone_data: dict) -> None:
        """Should deserialize from JSON."""
        schema = OTPNotificationSchema(**valid_phone_data)
        json_str = schema.model_dump_json()
        restored = OTPNotificationSchema.model_validate_json(json_str)
        assert restored.phone == schema.phone
        assert restored.secret_code == schema.secret_code
