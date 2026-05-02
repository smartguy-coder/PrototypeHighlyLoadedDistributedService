from __future__ import annotations

import logging
import os
import socket
import traceback
from typing import Any

# ============================================================================
# Logging — structured JSON for ClickHouse via Vector
# ============================================================================
# Every log record must carry ALL fields that match the ClickHouse schema:
#
#   timestamp, environment, service, host, level, log_type, logger,
#   trace_id, span_id, user_id, request_id, message, exception, extra
#
# The ClickHouseFieldsFilter guarantees these fields exist on every record
# (with sensible defaults) so Vector never fails on a missing column.
# ============================================================================

_SERVICE_NAME = os.getenv("SERVICE_NAME", "storefront-catalog-service")
_ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
_HOST = socket.gethostname()


class ClickHouseFieldsFilter(logging.Filter):
    """Inject default values for all ClickHouse schema fields.

    Run as a handler-level filter so it applies to every record that
    reaches the console handler, regardless of which logger emitted it.

    Side-effects on ``LogRecord``:
    - Adds ``level``   alias for ``levelname``  (ClickHouse column name)
    - Adds ``logger``  alias for ``name``        (ClickHouse column name)
    - Fills missing ClickHouse-specific fields with safe defaults
    - Serialises ``exc_info`` into the ``exception`` field as a plain string
    """

    _DEFAULTS: dict[str, object] = {
        "trace_id": "",
        "span_id": "",
        "user_id": None,
        "request_id": "",
        "log_type": "app",
        "service": _SERVICE_NAME,
        "environment": _ENVIRONMENT,
        "host": _HOST,
        "exception": "",
        "extra": "",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        # Rename standard fields to match ClickHouse column names
        record.level = record.levelname  # type: ignore[attr-defined]
        record.logger = record.name  # type: ignore[attr-defined]

        # Inject missing fields with defaults
        for field, default in self._DEFAULTS.items():
            if not hasattr(record, field):
                setattr(record, field, default)

        # Capture exc_info → exception field (plain text, not JSON-escaped)
        if record.exc_info and not getattr(record, "exception", ""):
            record.exception = "".join(  # type: ignore[attr-defined]
                traceback.format_exception(*record.exc_info)
            )

        return True


LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    "filters": {
        "clickhouse_fields": {
            "()": "settings.settings_logging.ClickHouseFieldsFilter",
        },
    },
    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------
    # `pythonjsonlogger` picks up %(field)s names from the format string
    # and emits them as JSON keys.  We use our aliased names (level,
    # logger) that were set by the filter above.
    # ------------------------------------------------------------------
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": (
                "%(asctime)s %(level)s %(logger)s %(message)s "
                "%(service)s %(environment)s %(host)s "
                "%(trace_id)s %(span_id)s "
                "%(user_id)s %(request_id)s "
                "%(log_type)s %(exception)s %(extra)s"
            ),
        },
    },
    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["clickhouse_fields"],
        },
    },
    # ------------------------------------------------------------------
    # Root logger — WARNING and above from third-party libs go to console
    # ------------------------------------------------------------------
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    # ------------------------------------------------------------------
    # App loggers
    # ------------------------------------------------------------------
    "loggers": {
        # All app code under the `apps` package
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Celery worker / beat logs
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Django request/server logs (keep at WARNING to avoid noise)
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
