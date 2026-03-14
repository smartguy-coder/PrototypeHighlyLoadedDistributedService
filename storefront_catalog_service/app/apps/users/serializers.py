from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


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


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone',
            'password',
            'first_name',
            'last_name',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        if not value:
            return None
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_phone(self, value):
        if not value:
            return None
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        
        if not email and not phone:
            raise serializers.ValidationError(
                {"detail": "Email or phone is required."}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read/update).
    """
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone',
            'first_name',
            'last_name',
            'is_email_verified',
            'is_phone_verified',
            'is_active',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'is_email_verified',
            'is_phone_verified',
            'is_active',
            'date_joined',
            'created_at',
            'updated_at',
        ]

    def validate_email(self, value):
        if not value:
            return None
        value = value.lower().strip()
        user = self.instance
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_phone(self, value):
        if not value:
            return None
        user = self.instance
        if User.objects.filter(phone=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("User with this phone already exists.")
        return value

    def validate(self, attrs):
        email = attrs.get('email', self.instance.email if self.instance else None)
        phone = attrs.get('phone', self.instance.phone if self.instance else None)
        
        if not email and not phone:
            raise serializers.ValidationError(
                {"detail": "User must have email or phone."}
            )
        return attrs
