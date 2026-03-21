from django.contrib import admin
from django.urls import include, path

from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.users.views import EmailOrPhoneTokenObtainPairView, OTPRequestView, OTPVerifyView

# Apply tags to SimpleJWT views
DecoratedTokenRefreshView = extend_schema(tags=["Authentication"])(TokenRefreshView)
DecoratedTokenVerifyView = extend_schema(tags=["Authentication"])(TokenVerifyView)


urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT token endpoints (password-based)
    path("api/v1/auth/token/", EmailOrPhoneTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/token/refresh/", DecoratedTokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/token/verify/", DecoratedTokenVerifyView.as_view(), name="token_verify"),
    # OTP authentication endpoints (passwordless)
    path("api/v1/auth/otp/request/", OTPRequestView.as_view(), name="otp_request"),
    path("api/v1/auth/otp/verify/", OTPVerifyView.as_view(), name="otp_verify"),
    # User endpoints
    path("api/v1/user/", include("apps.users.urls")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
