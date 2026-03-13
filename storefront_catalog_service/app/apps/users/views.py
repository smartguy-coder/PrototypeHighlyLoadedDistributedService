from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import EmailOrPhoneTokenObtainSerializer


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
                value={
                    "email": "user@example.com",
                    "password": "your_password"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Login with phone",
                description="Authenticate using phone number (E.164 format)",
                value={
                    "phone": "+380501234567",
                    "password": "your_password"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Both provided (email takes priority)",
                description="When both are provided, email is used for authentication",
                value={
                    "email": "user@example.com",
                    "phone": "+380501234567",
                    "password": "your_password"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Successful response",
                description="JWT token pair returned on successful authentication",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                },
                response_only=True,
            ),
        ],
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
