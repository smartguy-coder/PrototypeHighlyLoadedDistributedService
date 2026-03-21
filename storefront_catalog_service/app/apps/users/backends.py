from typing import Any

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest

from phonenumber_field.phonenumber import PhoneNumber

from apps.users.models import User


class EmailOrPhoneBackend(ModelBackend):
    """
    Authentication backend that supports login via email or phone.

    Usage in settings.py:
        AUTHENTICATION_BACKENDS = [
            'apps.users.backends.EmailOrPhoneBackend',
        ]
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> User | None:
        """
        Authenticate user by email or phone.

        Args:
            request: The HTTP request.
            username: Can be email or phone number.
            password: User password.
            **kwargs: Additional keyword arguments.

        Returns:
            User instance if authentication successful, None otherwise.
        """
        if username is None or password is None:
            return None

        try:
            phone_number = PhoneNumber.from_string(username, region=settings.PHONENUMBER_DEFAULT_REGION)
            if not phone_number.is_valid():
                phone_number = None
        except Exception:
            # Expected when username is email format, not a phone number
            phone_number = None

        try:
            if phone_number:
                user = User.objects.get(Q(email=username) | Q(phone=phone_number))
            else:
                user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Run password hashing to prevent timing attacks
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id: int) -> User | None:
        return User.objects.filter(pk=user_id).first()
