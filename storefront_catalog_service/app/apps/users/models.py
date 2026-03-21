import hashlib
import secrets
import string
from datetime import timedelta
from typing import ClassVar, Self

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from phonenumber_field.modelfields import PhoneNumberField

from apps.users.managers import CustomUserManager
from orm import BOOLEAN_DEFAULT_FALSE, NULLABLE_INDEXED, NULLABLE_UNIQUE_INDEXED, CreatedAtUpdatedAtMixin


class User(CreatedAtUpdatedAtMixin, AbstractUser):
    """
    Custom user model with email/phone authentication support.
    """

    username = None  # type: ignore[assignment]  # no default username
    email = models.EmailField(  # type: ignore[assignment]
        "email address", **NULLABLE_UNIQUE_INDEXED
    )
    phone = PhoneNumberField("phone number", **NULLABLE_UNIQUE_INDEXED)

    is_email_verified = models.BooleanField("email verified", **BOOLEAN_DEFAULT_FALSE)
    is_phone_verified = models.BooleanField("phone verified", **BOOLEAN_DEFAULT_FALSE)

    objects: ClassVar[CustomUserManager] = CustomUserManager()  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name="user_has_email_or_phone",
            ),
        ]

    def __str__(self) -> str:
        return self.email or str(self.phone) or f"User {self.pk}"

    def clean(self) -> None:
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)


class OTPCode(CreatedAtUpdatedAtMixin):
    """
    One-Time Password code for passwordless authentication.

    Flow:
    1. User requests OTP for email/phone
    2. System generates 10-digit code:
       - First 6 digits (verification_code) - shown to user immediately
       - Last 4 digits (secret_code) - sent via email/SMS (logged for now)
    3. User submits email/phone + verification_code + secret_code to login
    4. If valid: user is found/created and JWT tokens returned
    """

    OTP_VALIDITY_MINUTES: int = 5
    VERIFICATION_CODE_LENGTH: int = 6
    SECRET_CODE_LENGTH: int = 4

    email = models.EmailField("email address", **NULLABLE_INDEXED)
    phone = PhoneNumberField("phone number", **NULLABLE_INDEXED)
    verification_code = models.CharField(
        help_text="6-digit code shown to user (for identifying the OTP request)",
        max_length=6,
        db_index=True,
    )
    secret_code_hash = models.CharField(
        help_text="SHA-256 hash of 4-digit secret code (sent via email/SMS)",
        max_length=64,
    )
    expires_at = models.DateTimeField("expires at", db_index=True)
    is_used = models.BooleanField("is used", **BOOLEAN_DEFAULT_FALSE)

    class Meta:
        verbose_name = "OTP code"
        verbose_name_plural = "OTP codes"
        indexes = [
            models.Index(fields=["email", "verification_code", "is_used"]),
            models.Index(fields=["phone", "verification_code", "is_used"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name="otp_has_email_or_phone",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(email__isnull=False, phone__isnull=True)
                    | models.Q(email__isnull=True, phone__isnull=False)
                ),
                name="otp_has_email_xor_phone",
            ),
        ]

    def __str__(self) -> str:
        target = self.email or str(self.phone)
        return f"OTP {self.verification_code} for {target}"

    @classmethod
    def hash_secret(cls, secret_code: str) -> str:
        return hashlib.sha256(secret_code.encode()).hexdigest()

    @classmethod
    def generate_codes(cls) -> tuple[str, str]:
        verification_code = "".join(secrets.choice(string.digits) for _ in range(cls.VERIFICATION_CODE_LENGTH))
        secret_code = "".join(secrets.choice(string.digits) for _ in range(cls.SECRET_CODE_LENGTH))
        return verification_code, secret_code

    @classmethod
    def create_otp(cls, email: str | None = None, phone: str | None = None) -> tuple[Self, str]:
        if not email and not phone:
            raise ValueError("Either email or phone must be provided")
        if email and phone:
            raise ValueError("Only one of email or phone must be provided")

        verification_code, secret_code = cls.generate_codes()

        otp = cls.objects.create(
            email=email.lower().strip() if email else None,
            phone=phone if phone else None,
            verification_code=verification_code,
            secret_code_hash=cls.hash_secret(secret_code),
            expires_at=timezone.now() + timedelta(minutes=cls.OTP_VALIDITY_MINUTES),
        )

        return otp, secret_code

    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() < self.expires_at

    def verify_secret(self, secret_code: str) -> bool:
        return self.secret_code_hash == self.hash_secret(secret_code)

    def mark_as_used(self) -> None:
        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])
