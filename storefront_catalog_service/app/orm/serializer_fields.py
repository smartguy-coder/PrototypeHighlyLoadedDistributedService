"""
Custom serializer fields for Django REST Framework.
"""

from typing import Any

from rest_framework import serializers

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumber


class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        "invalid": "Enter a valid phone number.",
        "invalid_country_code": "Invalid country code.",
        "too_short": "Phone number is too short.",
        "too_long": "Phone number is too long.",
    }

    def __init__(self, region: str | None = None, store_with_plus: bool = False, **kwargs: Any) -> None:
        self.region = region
        self.store_with_plus = store_with_plus
        super().__init__(**kwargs)

    def to_internal_value(self, value: Any) -> str | None:  # type: ignore[override]
        value = super().to_internal_value(value)

        if not value:
            return None

        cleaned = value.strip()

        if not cleaned.startswith("+"):
            cleaned = f"+{cleaned}"

        phone_number: PhoneNumber
        try:
            phone_number = phonenumbers.parse(cleaned, self.region)
        except NumberParseException as e:
            error_type = e.error_type
            if error_type == NumberParseException.INVALID_COUNTRY_CODE:
                self.fail("invalid_country_code")
            elif error_type == NumberParseException.TOO_SHORT_NSN:
                self.fail("too_short")
            elif error_type == NumberParseException.TOO_LONG:
                self.fail("too_long")
            else:
                self.fail("invalid")
            # This line is unreachable but helps mypy understand the flow
            raise  # pragma: no cover

        if not phonenumbers.is_valid_number(phone_number):
            self.fail("invalid")

        formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)

        if self.store_with_plus:
            return formatted

        return formatted.lstrip("+")

    def to_representation(self, value: Any) -> str | None:  # type: ignore[override]
        if not value:
            return None

        # Convert PhoneNumber object to string if needed
        str_value = str(value)

        if str_value and not str_value.startswith("+"):
            return f"+{str_value}"

        return str_value
