from dataclasses import dataclass

from django.db import transaction

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import OTPCode, User


class OTPError(Exception):
    """Base exception for OTP-related errors."""


class OTPNotFoundError(OTPError):
    """OTP code not found."""


class OTPExpiredError(OTPError):
    """OTP code has expired."""


class OTPInvalidSecretError(OTPError):
    """Invalid secret code."""


@dataclass(frozen=True, slots=True)
class TokenPair:
    """JWT token pair."""

    refresh: str
    access: str


def find_valid_otp(*, email: str | None, phone: str | None, verification_code: str) -> OTPCode:
    filters = {
        "verification_code": verification_code,
        "is_used": False,
    }

    if email:
        filters["email"] = email.strip().lower()
    else:
        filters["phone"] = phone

    otp = OTPCode.objects.filter(**filters).order_by("-id").first()

    if not otp:
        raise OTPNotFoundError("Invalid verification code.")

    if not otp.is_valid():
        raise OTPExpiredError("OTP has expired.")

    return otp


def verify_otp_secret(otp: OTPCode, secret_code: str) -> None:
    if not otp.verify_secret(secret_code):
        raise OTPInvalidSecretError("Invalid secret code.")


@transaction.atomic
def get_or_create_verified_user(*, email: str | None, phone: str | None) -> User:
    """
    Get existing user or create new one with verified contact.

    For existing users, marks their email/phone as verified.
    For new users, creates account with unusable password.
    """
    if email:
        return _get_or_create_user_by_email(email)
    return _get_or_create_user_by_phone(phone)  # type: ignore[arg-type]


def _get_or_create_user_by_email(email: str) -> User:
    user = User.objects.filter(email=email).first()

    if user:
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified", "updated_at"])
        return user

    user = User.objects.create_user(
        email=email,
        password=None,
        is_email_verified=True,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


def _get_or_create_user_by_phone(phone: str) -> User:
    user = User.objects.filter(phone=phone).first()

    if user:
        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified", "updated_at"])
        return user

    user = User.objects.create_user(
        phone=phone,
        password=None,
        is_phone_verified=True,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


def generate_tokens(user: User) -> TokenPair:
    """Generate JWT token pair for user."""
    refresh = RefreshToken.for_user(user)
    return TokenPair(
        refresh=str(refresh),
        access=str(refresh.access_token),
    )
