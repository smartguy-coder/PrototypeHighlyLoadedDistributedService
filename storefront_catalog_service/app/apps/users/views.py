from typing import Any

from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.models import User
from apps.users.serializers import (
    EmailOrPhoneTokenObtainSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserCreateSerializer,
    UserSerializer,
)


class EmailOrPhoneTokenObtainPairView(TokenObtainPairView):
    """
    JWT token obtain view that supports login via email or phone.

    If both email and phone are provided, email takes precedence.
    """

    serializer_class = EmailOrPhoneTokenObtainSerializer

    @extend_schema(
        summary="Obtain JWT token pair",
        description="""
Authenticate user and obtain JWT access/refresh token pair.

## Authentication Methods

You can authenticate using **email** OR **phone number**:

| Field | Required | Description |
|-------|----------|-------------|
| `email` | No* | User's email address |
| `phone` | No* | Phone number in E.164 format (e.g., `+380501234567`) |
| `password` | Yes | User's password |

\\* At least one of `email` or `phone` is required.

## Priority Rule

⚠️ **If both `email` and `phone` are provided, `email` takes precedence** and `phone` will be ignored.

## Response

Returns JWT token pair:
- `access` — short-lived access token (use in `Authorization: Bearer <token>` header)
- `refresh` — long-lived refresh token (use to obtain new access token)
        """,
        examples=[
            OpenApiExample(
                name="Login with email",
                description="Authenticate using email address",
                value={"email": "newuser@example.com", "password": "SecurePass123!"},
                request_only=True,
            ),
            OpenApiExample(
                name="Login with phone",
                description="Authenticate using phone number (E.164 format)",
                value={"phone": "+380501234567", "password": "SecurePass123!"},
                request_only=True,
            ),
            OpenApiExample(
                name="Both provided (email takes priority)",
                description="When both are provided, email is used for authentication",
                value={"email": "newuser@example.com", "phone": "+380501234567", "password": "SecurePass123!"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="JWT token pair returned on successful authentication",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                response_only=True,
            ),
        ],
        tags=["Authentication"],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)


class UserCreateView(generics.CreateAPIView[User]):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register new user",
        description=r"""
Create a new user account.

## Required Fields


| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | No* | User's email address |
| `phone` | string | No* | Phone number in E.164 format |
| `password` | string | Yes | Password (min 8 characters) |
| `first_name` | string | No | User's first name |
| `last_name` | string | No | User's last name |

\* At least one of `email` or `phone` is required.
        """,
        examples=[
            OpenApiExample(
                name="Register with email",
                description="Create account using email address",
                value={
                    "email": "newuser@example.com",
                    "password": "SecurePass123!",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Register with phone",
                description="Create account using phone number (E.164 format)",
                value={
                    "phone": "+380501234567",
                    "password": "SecurePass123!",
                    "first_name": "Jane",
                    "last_name": "Smith",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Register with email and phone",
                description="Create account with both email and phone",
                value={
                    "email": "newuser@example.com",
                    "phone": "+380501234567",
                    "password": "SecurePass123!",
                    "first_name": "Alex",
                    "last_name": "Johnson",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Minimal registration (email only)",
                description="Create account with only required fields",
                value={"email": "minimal@example.com", "password": "SecurePass123!"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="Newly created user data",
                value={
                    "id": 1,
                    "email": "newuser@example.com",
                    "phone": None,
                    "first_name": "John",
                    "last_name": "Doe",
                },
                response_only=True,
            ),
        ],
        tags=["User"],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().post(request, *args, **kwargs)


class CurrentUserView(generics.RetrieveUpdateAPIView[User]):
    """
    Retrieve or update the currently authenticated user's profile.

    GET: Returns the current user's profile information.
    PATCH/PUT: Updates the current user's profile (email, phone, first_name, last_name).
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user  # type: ignore[return-value]

    @extend_schema(
        summary="Get current user profile",
        description="Retrieve the profile information of the currently authenticated user.",
        tags=["User"],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update current user profile",
        description="""
Partially update the current user's profile. Only provided fields will be updated.

## Editable Fields

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | User's email address |
| `phone` | string | Phone number in E.164 format |
| `first_name` | string | User's first name |
| `last_name` | string | User's last name |

⚠️ **Note:** At least one of `email` or `phone` must remain on the account.
        """,
        examples=[
            OpenApiExample(
                name="Update email",
                description="Change user's email address",
                value={"email": "newemail@example.com"},
                request_only=True,
            ),
            OpenApiExample(
                name="Update phone",
                description="Change user's phone number",
                value={"phone": "+380509876543"},
                request_only=True,
            ),
            OpenApiExample(
                name="Update name",
                description="Change user's first and last name",
                value={"first_name": "Updated", "last_name": "Name"},
                request_only=True,
            ),
            OpenApiExample(
                name="Update multiple fields",
                description="Update several fields at once",
                value={"email": "updated@example.com", "first_name": "John", "last_name": "Updated"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="Updated user profile",
                value={
                    "id": 1,
                    "email": "updated@example.com",
                    "phone": "+380501234567",
                    "first_name": "John",
                    "last_name": "Updated",
                    "is_email_verified": False,
                    "is_phone_verified": True,
                    "is_active": True,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-03-18T14:25:00Z",
                },
                response_only=True,
            ),
        ],
        tags=["User"],
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Replace current user profile",
        description=r"""
Completely replace the current user's profile. All editable fields should be provided.

## Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | No* | User's email address |
| `phone` | string | No* | Phone number in E.164 format |
| `first_name` | string | No | User's first name |
| `last_name` | string | No | User's last name |

\* At least one of `email` or `phone` is required.
        """,
        examples=[
            OpenApiExample(
                name="Full profile update",
                description="Replace all user profile fields",
                value={
                    "email": "complete@example.com",
                    "phone": "+380501234567",
                    "first_name": "Complete",
                    "last_name": "Profile",
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Email-only profile",
                description="Replace profile with email only (removes phone)",
                value={"email": "emailonly@example.com", "phone": None, "first_name": "Email", "last_name": "User"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="Replaced user profile",
                value={
                    "id": 1,
                    "email": "complete@example.com",
                    "phone": "+380501234567",
                    "first_name": "Complete",
                    "last_name": "Profile",
                    "is_email_verified": False,
                    "is_phone_verified": False,
                    "is_active": True,
                    "date_joined": "2024-01-15T10:30:00Z",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-03-18T14:30:00Z",
                },
                response_only=True,
            ),
        ],
        tags=["User"],
    )
    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().put(request, *args, **kwargs)


# =============================================================================
# OTP Views
# =============================================================================


class OTPRequestView(generics.CreateAPIView):  # type: ignore[type-arg]
    """View for requesting OTP codes."""

    serializer_class = OTPRequestSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Request OTP code",
        description="""
Request a one-time password for passwordless authentication.

## How it works

1. Send your email or phone number
2. Receive a 6-digit **verification code** in the response
3. A 4-digit **secret code** is sent to your email/SMS (currently logged)
4. Use both codes with `/api/v1/auth/otp/verify/` to login

## Code Validity

⏱️ OTP codes are valid for **5 minutes**.

## Authentication Methods

| Field | Required | Description |
|-------|----------|-------------|
| `email` | No* | User's email address |
| `phone` | No* | Phone number in E.164 format |

\\* At least one of `email` or `phone` is required.
        """,
        examples=[
            OpenApiExample(
                name="Request OTP via email",
                description="Request OTP code sent to email",
                value={"email": "user@example.com"},
                request_only=True,
            ),
            OpenApiExample(
                name="Request OTP via phone",
                description="Request OTP code sent to phone (E.164 format)",
                value={"phone": "+380501234567"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="Verification code returned, secret code logged",
                value={"verification_code": "123456", "expires_at": "2026-03-18T15:35:00Z"},
                response_only=True,
            ),
        ],
        tags=["OTP Authentication"],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)


class OTPVerifyView(generics.CreateAPIView):  # type: ignore[type-arg]
    """View for verifying OTP codes and obtaining JWT tokens."""

    serializer_class = OTPVerifySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Verify OTP and login",
        description="""
Verify OTP codes and obtain JWT tokens for authentication.

## How it works

1. Provide your email/phone + verification_code (from request) + secret_code (from email/SMS)
2. If codes are valid:
   - **Existing user**: Logs in and marks email/phone as verified
   - **New user**: Creates account with verified email/phone (passwordless)
3. Returns JWT access and refresh tokens

## Two-Factor Authentication

This implements 2FA:
- **Factor 1**: Verification code (proves you initiated the request)
- **Factor 2**: Secret code (proves you own the email/phone)

## Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| `email` | No* | User's email address |
| `phone` | No* | Phone number in E.164 format |
| `verification_code` | Yes | 6-digit code from OTP request |
| `secret_code` | Yes | 4-digit code sent via email/SMS |

\\* At least one of `email` or `phone` is required.
        """,
        examples=[
            OpenApiExample(
                name="Verify with email",
                description="Complete OTP login with email",
                value={"email": "user@example.com", "verification_code": "123456", "secret_code": "1234"},
                request_only=True,
            ),
            OpenApiExample(
                name="Verify with phone",
                description="Complete OTP login with phone",
                value={"phone": "+380501234567", "verification_code": "654321", "secret_code": "4321"},
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="JWT tokens returned on successful verification",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                response_only=True,
            ),
        ],
        tags=["OTP Authentication"],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
