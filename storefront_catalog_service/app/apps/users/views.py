from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import EmailOrPhoneTokenObtainSerializer, UserSerializer, UserCreateSerializer


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


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register new user",
        description="""
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
        tags=["User"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the currently authenticated user's profile.
    
    GET: Returns the current user's profile information.
    PATCH/PUT: Updates the current user's profile (email, phone, first_name, last_name).
    """
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="Get current user profile",
        description="Retrieve the profile information of the currently authenticated user.",
        tags=["User"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update current user profile",
        tags=["User"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Replace current user profile",
        tags=["User"],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
