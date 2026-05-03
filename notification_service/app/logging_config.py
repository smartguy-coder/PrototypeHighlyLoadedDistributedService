"""
Logging configuration — structured JSON for ClickHouse via Vector.

Mirrors the configuration used in storefront_catalog_service so the
same Vector pipeline (vector.toml) ingests both services into
ClickHouse without any extra rules.

The shared utility ``build_logging_config`` does the heavy lifting:
schema fields, JSON formatter, console handler, and the filter that
guarantees every record carries the full ClickHouse column set. This
module only supplies notification-service-specific overrides for
third-party loggers (FastStream, aiokafka, uvicorn).
"""

from typing import Any

from config import settings
from prototype_highly_loaded_distributed_service_utils.logging import (
    build_logging_config,
)

# ---------------------------------------------------------------------------
# Per-logger overrides specific to this service.
#
# - ``aiokafka`` / ``kafka`` — chatty at INFO (per-partition fetch loops,
#   coordinator heartbeats). WARNING is enough to catch real issues.
# - ``faststream`` — INFO so subscriber lifecycle and message handling
#   appears in logs.
# - ``uvicorn*`` — uvicorn ships its own pre-installed text handlers.
#   Setting ``handlers: []`` removes them so access/error logs flow
#   through the JSON ``console`` handler from the root logger via
#   ``propagate=True``. Without this we'd get a mix of plain text and
#   JSON in the same stream and Vector would drop the text lines.
# ---------------------------------------------------------------------------
_EXTRA_LOGGERS: dict[str, dict[str, Any]] = {
    "aiokafka": {"level": "WARNING", "propagate": True},
    "kafka": {"level": "WARNING", "propagate": True},
    "faststream": {"level": "INFO", "propagate": True},
    "uvicorn": {"level": "INFO", "propagate": True, "handlers": []},
    "uvicorn.access": {"level": "INFO", "propagate": True, "handlers": []},
    "uvicorn.error": {"level": "INFO", "propagate": True, "handlers": []},
}

LOGGING: dict[str, Any] = build_logging_config(
    service_name=settings.SERVICE_NAME,
    environment=settings.ENVIRONMENT,
    host=settings.HOST,
    log_level=settings.LOG_LEVEL,
    extra_loggers=_EXTRA_LOGGERS,
)
