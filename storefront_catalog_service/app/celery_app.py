import logging.config
import os
from typing import Any

from django.conf import settings

from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

app = Celery("celery_app")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args: Any, **kwargs: Any) -> None:
    logging.config.dictConfig(settings.LOGGING)
