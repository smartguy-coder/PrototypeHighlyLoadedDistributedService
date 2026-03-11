from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class EmailOrPhoneTokenObtainSerializer(serializers.Serializer):
    """
    JWT token serializer that supports login via email or phone.
    
    Usage:
        POST /api/v1/auth/token/
        {"email": "user@example.com", "password": "secret"}
        OR
        {"phone": "+380501234567", "password": "secret"}
    """
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        phone = attrs.get('phone', '').strip()
        password = attrs.get('password')

        if not email and not phone:
            raise serializers.ValidationError(
                {"detail": "Email or phone is required."}
            )

        username = email if email else phone

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                {"detail": "No active account found with the given credentials"}
            )

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class EmailOrPhoneTokenObtainPairSerializer(EmailOrPhoneTokenObtainSerializer):
    """Alias for compatibility with SimpleJWT naming convention."""
    pass
