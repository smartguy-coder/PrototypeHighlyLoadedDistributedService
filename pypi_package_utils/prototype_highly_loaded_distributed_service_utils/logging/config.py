"""
Factory for the standard logging configuration used by all services
that ship logs through the Vector → ClickHouse pipeline.

The returned dict is suitable for ``logging.config.dictConfig``. It
configures:

- A single ``ClickHouseFieldsFilter`` that fills schema defaults.
- A single ``json`` formatter (``python-json-logger``) whose format
  string lists exactly the columns expected by ClickHouse.
- A single ``console`` handler that writes JSON to stdout, where the
  Docker runtime captures it and Vector tails it.
- A root logger at ``log_level`` and an optional ``extra_loggers``
  block for service-specific tweaks (Django, Celery, FastAPI, etc.).

Why a factory rather than a static dict: the schema defaults depend
on per-service identity (``service_name``, ``environment``, ``host``),
and each service ships with a different set of third-party loggers
that need their levels tuned. A factory accepts both as parameters
without forcing any caller to subclass or monkey-patch.
"""

from typing import Any

from prototype_highly_loaded_distributed_service_utils.logging.filters import ClickHouseFieldsFilter


# Format string for python-json-logger. Field names map 1:1 onto
# ClickHouse columns. ``asctime`` is the marker field that the Vector
# VRL transform uses to recognise our structured logs and discard
# everything else (boot banners, library noise, etc.).
_JSON_FORMAT = (
    "%(asctime)s %(level)s %(logger)s %(message)s "
    "%(service)s %(environment)s %(host)s "
    "%(trace_id)s %(span_id)s "
    "%(user_id)s %(request_id)s "
    "%(log_type)s %(exception)s %(extra)s"
)


def build_logging_config(
        *,
        service_name: str,
        environment: str,
        host: str,
        log_level: str = "INFO",
        extra_loggers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a ``logging.config.dictConfig``-compatible dict.

    Parameters
    ----------
    service_name:
        Value written to the ``service`` ClickHouse column. Should
        match the container name where reasonable, so log queries
        line up with ``docker ps`` output.
    environment:
        ``production`` / ``staging`` / ``development`` etc. Used as
        the ``environment`` ClickHouse column and surfaced in Grafana
        dashboards.
    host:
        Hostname of the process. Typically ``socket.gethostname()``,
        which inside Docker resolves to the container ID (or the
        ``hostname:`` value from compose).
    log_level:
        Level applied to the root logger. App loggers passed via
        ``extra_loggers`` can override this individually.
    extra_loggers:
        Per-logger overrides. Same shape as the ``loggers`` key of
        ``logging.config.dictConfig``. Use this to:
        - quiet down chatty third-party libraries (``aiokafka``)
        - set a different level for app code (``apps`` at ``INFO``
          when root is at ``WARNING``)
        - strip pre-installed handlers from frameworks that ship
          their own (``uvicorn``, ``uvicorn.access``)

        If a logger config does not specify ``handlers``, the root
        ``console`` handler is used via ``propagate``.

    Returns
    -------
    A fresh dict on every call. Safe to mutate by the caller before
    passing to ``dictConfig`` — the package keeps no shared state.
    """
    # Note: dictConfig resolves "()" as a callable factory. Passing
    # the class object directly is supported (cleaner than the
    # legacy "module.path.ClassName" string form, and survives
    # refactors / renames automatically). The remaining keys in this
    # sub-dict become kwargs to the constructor.
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "clickhouse_fields": {
                "()": ClickHouseFieldsFilter,
                "service_name": service_name,
                "environment": environment,
                "host": host,
            },
        },
        "formatters": {
            "json": {
                # python-json-logger ≥4 exposes the formatter at
                # ``pythonjsonlogger.json.JsonFormatter``.
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": _JSON_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["clickhouse_fields"],
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": dict(extra_loggers) if extra_loggers else {},
    }

    return config
