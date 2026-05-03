"""
Logging configuration for storefront-catalog-service.

The Vector pipeline (vector.toml) ingests stdout from this container
into ClickHouse. The shape of every log record must match the
ClickHouse ``logs`` table schema. That contract is implemented in
the shared utility package — this file is just the thin Django-side
wiring that supplies per-service identity and Django-specific logger
overrides.

See:
    - documentation/docs/technologies/clickhouse.md  (table schema)
    - documentation/docs/technologies/vector.md      (transform & pipeline)
    - prototype_highly_loaded_distributed_service_utils.logging
"""

from __future__ import annotations

import socket
from typing import Any

from decouple import config
from prototype_highly_loaded_distributed_service_utils.logging import (
    build_logging_config,
)

# ============================================================================
# Service identification — also imported by management commands & filters
# ============================================================================

SERVICE_NAME: str = config("SERVICE_NAME", default="storefront-catalog-service")
ENVIRONMENT: str = config("ENVIRONMENT", default="production")
HOST: str = socket.gethostname()

# ============================================================================
# ClickHouse — log storage (read by management commands; Vector reads its
# own credentials from environment variables in vector.toml)
# ============================================================================

CLICKHOUSE_HOST: str = config("CLICKHOUSE_HOST", default="localhost")
CLICKHOUSE_PORT: int = config("CLICKHOUSE_PORT", default=8123, cast=int)
CLICKHOUSE_USER: str = config("CLICKHOUSE_USER", default="default")
CLICKHOUSE_PASSWORD: str = config("CLICKHOUSE_PASSWORD", default="")

# ============================================================================
# Logging — structured JSON for ClickHouse via Vector
# ============================================================================
# The shared utility builds the bulk of LOGGING; we only specify Django- and
# Celery-specific logger overrides here. Notes on the choices below:
#
# - ``apps``  — INFO is loud enough to trace business actions but quiet
#   enough not to drown the table. The ``apps`` prefix matches the
#   layout enforced by import-linter (see pyproject.toml).
# - ``django`` — WARNING because INFO produces one line per request.
# - ``django.request`` — ERROR; Django emits 4xx as WARNING and 5xx as
#   ERROR, and 4xx noise (404 from scanners etc.) isn't worth keeping.
# - ``celery`` and ``celery.task`` — INFO captures task lifecycle events
#   that are essential for debugging the queue.
#
# ``propagate=False`` on every entry: each logger has the ``console``
# handler attached directly, so propagation up to root would duplicate
# every record. Root stays at WARNING for any third-party library that
# isn't explicitly listed.
# ============================================================================

LOGGING: dict[str, Any] = build_logging_config(
    service_name=SERVICE_NAME,
    environment=ENVIRONMENT,
    host=HOST,
    log_level="WARNING",
    extra_loggers={
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
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
)
