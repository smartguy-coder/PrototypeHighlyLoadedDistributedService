from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.users.views import EmailOrPhoneTokenObtainPairView


urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns_drf = [
    path('api/v1/auth/token/', EmailOrPhoneTokenObtainPairView.as_view()),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view()),
    path('api/v1/auth/token/verify/', TokenVerifyView.as_view()),
    path("api/schema/", SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]


urlpatterns += urlpatterns_drf
