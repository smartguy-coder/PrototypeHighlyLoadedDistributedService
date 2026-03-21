import logging
from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import OTPCode, User
from orm import PhoneNumberField

logger = logging.getLogger(__name__)


class EmailOrPhoneTokenObtainSerializer(serializers.Serializer[dict[str, str]]):
    """
    JWT token serializer that supports login via email or phone.

    Usage:
        POST /api/v1/auth/token/
        {"email": "user@example.com", "password": "secret"}
        OR
        {"phone": "+380501234567", "password": "secret"}
    """

    email = serializers.EmailField(required=False, allow_blank=True)
    phone = PhoneNumberField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        email = attrs.get("email", "").strip()
        phone = attrs.get("phone")  # PhoneNumber object or None
        password = attrs.get("password")

        if not email and not phone:
            raise serializers.ValidationError({"detail": "Email or phone is required."})

        username = email if email else str(phone)

        user = authenticate(
            request=self.context.get("request"),
            username=username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError({"detail": "No active account found with the given credentials"})

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class EmailOrPhoneTokenObtainPairSerializer(EmailOrPhoneTokenObtainSerializer):
    """Alias for compatibility with SimpleJWT naming convention."""


class UserCreateSerializer(serializers.ModelSerializer[User]):
    """
    Serializer for user registration.
    """

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = PhoneNumberField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "password",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value: str | None) -> str | None:
        if not value:
            return None
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_phone(self, value: str | None) -> str | None:
        """Check phone uniqueness after normalization."""
        if not value:
            return None
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        return value

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        phone = attrs.get("phone")

        if not email and not phone:
            raise serializers.ValidationError({"detail": "Email or phone is required."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        return User.objects.create_user(**validated_data)


# =============================================================================
# User Profile Serializers
# =============================================================================


class UserSerializer(serializers.ModelSerializer[User]):
    """
    Serializer for user profile (read/update).
    """

    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = PhoneNumberField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_email_verified",
            "is_phone_verified",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_email_verified",
            "is_phone_verified",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value: str | None) -> str | None:
        if not value:
            return None
        value = value.lower().strip()
        user = self.instance
        if user and User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_phone(self, value: str | None) -> str | None:
        """Check phone uniqueness after normalization, excluding current user."""
        if not value:
            return None
        user = self.instance
        if user and User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email", self.instance.email if self.instance else None)
        phone = attrs.get("phone", self.instance.phone if self.instance else None)

        if not email and not phone:
            raise serializers.ValidationError({"detail": "User must have email or phone."})
        return attrs


# =============================================================================
# OTP Serializers
# =============================================================================


class OTPRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """for more info - look into view extended schema"""

    email = serializers.EmailField(required=False, allow_blank=True)
    phone = PhoneNumberField(required=False, allow_blank=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        phone = attrs.get("phone")  # PhoneNumber object or None

        if not email and not phone:
            raise serializers.ValidationError({"detail": "Email or phone is required."})

        if email:
            attrs["email"] = email.strip().lower()
            attrs["phone"] = None
        else:
            attrs["email"] = None
            attrs["phone"] = str(phone)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> dict[str, Any]:
        email = validated_data.get("email")
        phone = validated_data.get("phone")

        otp, secret_code = OTPCode.create_otp(email=email, phone=phone)
        target = email or phone

        # todo Log the secret code (in production, this would be sent via email/SMS)
        logger.info(f"OTP secret code for {target}: {secret_code}")

        return {
            "verification_code": otp.verification_code,
            "expires_at": otp.expires_at,
        }


class OTPVerifySerializer(serializers.Serializer[dict[str, str]]):
    """for more info - look into view extended schema"""

    email = serializers.EmailField(required=False, allow_blank=True)
    phone = PhoneNumberField(required=False, allow_blank=True)
    verification_code = serializers.CharField(
        min_length=6, max_length=6, help_text="6-digit verification code received when requesting OTP"
    )
    secret_code = serializers.CharField(min_length=4, max_length=4, help_text="4-digit secret code sent via email/SMS")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email")
        phone = attrs.get("phone")  # PhoneNumber object or None
        verification_code = attrs.get("verification_code", "").strip()
        secret_code = attrs.get("secret_code", "").strip()

        if not email and not phone:
            raise serializers.ValidationError({"detail": "Email or phone is required."})

        # Find the OTP
        otp: OTPCode | None
        if email:
            otp = (
                OTPCode.objects.filter(
                    email=email.strip().lower(),
                    verification_code=verification_code,
                    is_used=False,
                )
                .order_by("-id")
                .first()
            )
        else:
            otp = (
                OTPCode.objects.filter(
                    phone=phone,
                    verification_code=verification_code,
                    is_used=False,
                )
                .order_by("-id")
                .first()
            )

        if not otp:
            raise serializers.ValidationError({"detail": "Invalid verification code."})

        if not otp.is_valid():
            raise serializers.ValidationError({"detail": "OTP has expired."})

        if not otp.verify_secret(secret_code):
            raise serializers.ValidationError({"detail": "Invalid secret code."})

        attrs["otp"] = otp
        attrs["email"] = email
        attrs["phone"] = str(phone) if phone else None

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> dict[str, str]:
        otp: OTPCode = validated_data["otp"]
        email = validated_data.get("email")
        phone = validated_data.get("phone")

        otp.mark_as_used()

        user: User
        if email:
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                # Existing user - mark email as verified
                if not existing_user.is_email_verified:
                    existing_user.is_email_verified = True
                    existing_user.save(update_fields=["is_email_verified", "updated_at"])
                user = existing_user
            else:
                # New user - create with verified email and unusable password
                user = User.objects.create_user(
                    email=email,
                    password=None,  # Will set unusable password
                    is_email_verified=True,
                )
                user.set_unusable_password()
                user.save()
        else:
            existing_user = User.objects.filter(phone=phone).first()
            if existing_user:
                # Existing user - mark phone as verified
                if not existing_user.is_phone_verified:
                    existing_user.is_phone_verified = True
                    existing_user.save(update_fields=["is_phone_verified"])
                user = existing_user
            else:
                # New user - create with verified phone and unusable password
                user = User.objects.create_user(
                    phone=phone,
                    password=None,
                    is_phone_verified=True,
                )
                user.set_unusable_password()
                user.save()

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
