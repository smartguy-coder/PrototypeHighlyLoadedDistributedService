from pathlib import Path  # type: ignore

from decouple import Csv, config

from settings.settings_auth import *  # noqa: F403  # type: ignore
from settings.settings_celery import *  # noqa: F403  # type: ignore
from settings.settings_databases import *  # noqa: F403  # type: ignore
from settings.settings_drf import *  # noqa: F403  # type: ignore
from settings.settings_kafka import *  # noqa: F403  # type: ignore
from settings.settings_logging import *  # noqa: F403  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY: Use environment variable in production, fallback to insecure key for development only
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-6ck=mw17c(b6l$lm9-z@5qf*99*1zm(0q%cmosxz(i+0*f_58v",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "corsheaders",
    "phonenumber_field",
    "drf_spectacular",
    "rest_framework_simplejwt",
    "rest_framework",
    "django_celery_beat",
    # Local apps
    "apps.users",
    "apps.services",
    "apps.catalog",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Phone Number Field Settings
PHONENUMBER_DEFAULT_REGION = None  # Require country code (e.g., +380, +1)
PHONENUMBER_DEFAULT_FORMAT = "E164"
