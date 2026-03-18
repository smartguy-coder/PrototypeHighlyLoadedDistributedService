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
                    "email": "newuser@example.com",
                    "password": "SecurePass123!"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Login with phone",
                description="Authenticate using phone number (E.164 format)",
                value={
                    "phone": "+380501234567",
                    "password": "SecurePass123!"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Both provided (email takes priority)",
                description="When both are provided, email is used for authentication",
                value={
                    "email": "newuser@example.com",
                    "phone": "+380501234567",
                    "password": "SecurePass123!"
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
        examples=[
            OpenApiExample(
                name="Register with email",
                description="Create account using email address",
                value={
                    "email": "newuser@example.com",
                    "password": "SecurePass123!",
                    "first_name": "John",
                    "last_name": "Doe"
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
                    "last_name": "Smith"
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
                    "last_name": "Johnson"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Minimal registration (email only)",
                description="Create account with only required fields",
                value={
                    "email": "minimal@example.com",
                    "password": "SecurePass123!"
                },
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
                    "last_name": "Doe"
                },
                response_only=True,
            ),
        ],
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
                value={
                    "email": "newemail@example.com"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Update phone",
                description="Change user's phone number",
                value={
                    "phone": "+380509876543"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Update name",
                description="Change user's first and last name",
                value={
                    "first_name": "Updated",
                    "last_name": "Name"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Update multiple fields",
                description="Update several fields at once",
                value={
                    "email": "updated@example.com",
                    "first_name": "John",
                    "last_name": "Updated"
                },
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
                    "updated_at": "2024-03-18T14:25:00Z"
                },
                response_only=True,
            ),
        ],
        tags=["User"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Replace current user profile",
        description="""
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
                    "last_name": "Profile"
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Email-only profile",
                description="Replace profile with email only (removes phone)",
                value={
                    "email": "emailonly@example.com",
                    "phone": None,
                    "first_name": "Email",
                    "last_name": "User"
                },
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
                    "updated_at": "2024-03-18T14:30:00Z"
                },
                response_only=True,
            ),
        ],
        tags=["User"],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
