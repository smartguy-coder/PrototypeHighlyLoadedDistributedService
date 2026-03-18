"""
Custom serializer fields for Django REST Framework.
"""

import phonenumbers
from phonenumbers import NumberParseException

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PhoneNumberField(serializers.CharField):
    default_error_messages = {
        'invalid': 'Enter a valid phone number.',
        'invalid_country_code': 'Invalid country code.',
        'too_short': 'Phone number is too short.',
        'too_long': 'Phone number is too long.',
    }

    def __init__(self, region: str | None = None, store_with_plus: bool = False, **kwargs):
        self.region = region
        self.store_with_plus = store_with_plus
        super().__init__(**kwargs)

    def to_internal_value(self, value: str) -> str | None:
        value = super().to_internal_value(value)

        if not value:
            return value

        cleaned = value.strip()

        if not cleaned.startswith('+'):
            cleaned = f'+{cleaned}'

        phone_number = cleaned
        try:
            phone_number = phonenumbers.parse(cleaned, self.region)
        except NumberParseException as e:
            error_type = e.error_type
            if error_type == NumberParseException.INVALID_COUNTRY_CODE:
                self.fail('invalid_country_code')
            elif error_type == NumberParseException.TOO_SHORT_NSN:
                self.fail('too_short')
            elif error_type == NumberParseException.TOO_LONG:
                self.fail('too_long')
            else:
                self.fail('invalid')

        if not phonenumbers.is_valid_number(phone_number):
            self.fail('invalid')

        formatted = phonenumbers.format_number(
            phone_number,
            phonenumbers.PhoneNumberFormat.E164
        )

        if self.store_with_plus:
            return formatted

        return formatted.lstrip('+')

    def to_representation(self, value: str) -> str:
        if not value:
            return value

        if value and not value.startswith('+'):
            return f'+{value}'

        return value
