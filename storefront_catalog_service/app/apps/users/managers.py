from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import User


class CustomUserManager(BaseUserManager["User"]):
    """
    Custom user model manager.
    Supports authentication via email or phone.
    """

    def create_user(
        self,
        email: str | None = None,
        phone: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        if not email and not phone:
            raise ValueError("User must have an email or phone number")

        if email:
            email = self.normalize_email(email).lower()

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str | None = None,
        phone: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, phone=phone, password=password, **extra_fields)
