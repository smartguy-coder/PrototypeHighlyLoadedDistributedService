from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from orm import (
    BOOLEAN_DEFAULT_FALSE,
    NULLABLE_UNIQUE_INDEXED,
    CreatedAtUpdatedAtMixin,
)

from apps.users.managers import CustomUserManager


class User(CreatedAtUpdatedAtMixin, AbstractUser):
    """
    Custom user model with email/phone authentication support.
    """

    username = None  # no default username
    email = models.EmailField("email address", **NULLABLE_UNIQUE_INDEXED)
    phone = PhoneNumberField("phone number", **NULLABLE_UNIQUE_INDEXED)

    is_email_verified = models.BooleanField("email verified", **BOOLEAN_DEFAULT_FALSE)
    is_phone_verified = models.BooleanField("phone verified", **BOOLEAN_DEFAULT_FALSE)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name="user_has_email_or_phone",
            ),
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

