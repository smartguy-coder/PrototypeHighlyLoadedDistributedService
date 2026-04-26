from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone as dj_timezone

from celery import Task, shared_task

from apps.users.models import OTPCode

logger = logging.getLogger(__name__)


@shared_task(queue="default", bind=True)
def simple_task_with_defined_time(self: Task[..., None], data: Any) -> None:
    # use apply_async + eta param
    logger.info(
        "[simple_task_with_defined_time] started | task_id=%s retries=%s  data=%s",
        self.request.id,
        self.request.retries,
        data,
    )
    logger.info("[simple_task_with_defined_time] finished successfully | task_id=%s", self.request.id)


@shared_task(queue="default", bind=True, name="users.cleanup_expired_otp_codes")
def cleanup_expired_otp_codes(self: Task[..., None]) -> None:
    """Delete OTPCode records that expired more than 5 minutes ago."""
    cutoff = dj_timezone.now()
    deleted_count, _ = OTPCode.objects.filter(expires_at__lt=cutoff).delete()
    logger.info(
        "[cleanup_expired_otp_codes] deleted %d expired OTP codes | task_id=%s",
        deleted_count,
        self.request.id,
    )
