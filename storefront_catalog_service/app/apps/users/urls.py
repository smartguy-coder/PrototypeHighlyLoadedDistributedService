from django.urls import path

from apps.users.views import CurrentUserView, UserCreateView


urlpatterns = [
    path('register/', UserCreateView.as_view(), name='user_register'),
    path('', CurrentUserView.as_view(), name='current_user'),
]
