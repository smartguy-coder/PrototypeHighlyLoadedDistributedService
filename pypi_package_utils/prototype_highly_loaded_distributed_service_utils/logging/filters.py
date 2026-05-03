"""
Logging filter that ensures every LogRecord carries the full set of
ClickHouse schema columns expected by the Vector → ClickHouse pipeline.

This filter is the contract between application code and the storage
layer: as long as it is attached to the JSON-emitting handler, the
schema invariant holds regardless of which logger emitted the record
or which fields the caller chose to pass via ``extra=``.
"""

from __future__ import annotations

import logging
import traceback


class ClickHouseFieldsFilter(logging.Filter):
    """Inject default values for all ClickHouse schema fields.

    Run as a handler-level filter so it applies to every record that
    reaches the JSON console handler, regardless of which logger
    emitted it.

    Side-effects on ``LogRecord``:
    - Adds ``level``   alias for ``levelname``  (ClickHouse column name)
    - Adds ``logger``  alias for ``name``        (ClickHouse column name)
    - Fills missing ClickHouse-specific fields with safe defaults
    - Serialises ``exc_info`` into the ``exception`` field as plain text

    Service identity (``service``, ``environment``, ``host``) is supplied
    by the caller at construction time. This keeps the package free of
    any environment-variable / settings-framework coupling — Django apps
    use ``decouple``, FastAPI apps use ``pydantic-settings``, and CLI
    tools may pass values inline. The filter doesn't care.
    """

    def __init__(
        self,
        *,
        service_name: str,
        environment: str,
        host: str,
        name: str = "",
    ) -> None:
        super().__init__(name=name)
        self._defaults: dict[str, object] = {
            "trace_id": "",
            "span_id": "",
            "user_id": None,
            "request_id": "",
            "log_type": "app",
            "service": service_name,
            "environment": environment,
            "host": host,
            "exception": "",
            "extra": "",
        }

    def filter(self, record: logging.LogRecord) -> bool:
        # Rename standard fields to match ClickHouse column names so the
        # JSON formatter's "%(level)s %(logger)s ..." format string maps
        # 1:1 onto schema columns.
        record.level = record.levelname  # type: ignore[attr-defined]
        record.logger = record.name  # type: ignore[attr-defined]

        # Inject missing fields with defaults. Existing values from
        # ``logger.info(..., extra={...})`` calls are preserved.
        for field, default in self._defaults.items():
            if not hasattr(record, field):
                setattr(record, field, default)

        # Capture exc_info → exception field as plain text. ClickHouse
        # stores this in a String column; embedding a JSON-escaped blob
        # there would make grep / LIKE queries painful.
        if record.exc_info and not getattr(record, "exception", ""):
            record.exception = "".join(  # type: ignore[attr-defined]
                traceback.format_exception(*record.exc_info)
            )

        return True
