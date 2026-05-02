"""
Logging configuration — structured JSON for ClickHouse via Vector.

Mirrors the schema used in storefront_catalog_service so the same
Vector pipeline (vector.toml) ingests both services into ClickHouse
without any extra rules.

Every log record must carry ALL fields that match the ClickHouse schema:

    timestamp, environment, service, host, level, log_type, logger,
    trace_id, span_id, user_id, request_id, message, exception, extra

The ClickHouseFieldsFilter guarantees these fields exist on every record
(with sensible defaults) so Vector never fails on a missing column.
"""

import logging
import traceback
from typing import Any

from config import settings


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
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT,
        "host": settings.HOST,
        "exception": "",
        "extra": "",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        # Rename standard fields to match ClickHouse column names
        record.level = record.levelname
        record.logger = record.name

        # Inject missing fields with defaults
        for field, default in self._DEFAULTS.items():
            if not hasattr(record, field):
                setattr(record, field, default)

        # Capture exc_info → exception field (plain text, not JSON-escaped)
        if record.exc_info and not getattr(record, "exception", ""):
            record.exception = "".join(traceback.format_exception(*record.exc_info))

        return True


LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    "filters": {
        "clickhouse_fields": {
            "()": "logging_config.ClickHouseFieldsFilter",
        },
    },
    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------
    # `pythonjsonlogger` picks up %(field)s names from the format string
    # and emits them as JSON keys.  We use our aliased names (level,
    # logger) that were set by the filter above. `asctime` is required
    # by the Vector pipeline — it parses it as the event timestamp.
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
    # Root logger — everything propagates here and goes through the JSON
    # console handler. Per-logger entries below only tweak levels and
    # strip uvicorn's pre-installed text handlers so all logs are JSON.
    # ------------------------------------------------------------------
    "root": {
        "handlers": ["console"],
        "level": settings.LOG_LEVEL,
    },
    "loggers": {
        # Quiet down chatty Kafka clients
        "aiokafka": {"level": "WARNING", "propagate": True},
        "kafka": {"level": "WARNING", "propagate": True},
        # FastStream framework
        "faststream": {"level": "INFO", "propagate": True},
        # Uvicorn ships its own text handlers by default — drop them so
        # access/error logs flow through our JSON pipeline only.
        "uvicorn": {"level": "INFO", "propagate": True, "handlers": []},
        "uvicorn.access": {"level": "INFO", "propagate": True, "handlers": []},
        "uvicorn.error": {"level": "INFO", "propagate": True, "handlers": []},
    },
}
