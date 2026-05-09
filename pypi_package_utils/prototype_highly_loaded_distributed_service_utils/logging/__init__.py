"""
Structured logging utilities for the ClickHouse logging pipeline.

The resulting JSON on stdout matches the ClickHouse ``logs`` table
schema so Vector's VRL transform can pass each line through with
minimal reshaping.

Usage (Django, ``settings.py``):

    from prototype_highly_loaded_distributed_service_utils.logging import (
        build_logging_config,
    )

    LOGGING = build_logging_config(
        service_name=SERVICE_NAME,
        environment=ENVIRONMENT,
        host=HOST,
        extra_loggers={
            "apps":           {"level": "INFO",    "propagate": True},
            "django":         {"level": "WARNING", "propagate": True},
            "django.request": {"level": "ERROR",   "propagate": True},
        },
    )

Usage (FastAPI / FastStream):

    import logging.config
    from prototype_highly_loaded_distributed_service_utils.logging import (
        build_logging_config,
    )

    logging.config.dictConfig(build_logging_config(
        service_name=settings.SERVICE_NAME,
        environment=settings.ENVIRONMENT,
        host=settings.HOST,
        log_level=settings.LOG_LEVEL,
        extra_loggers={
            "uvicorn":        {"level": "INFO", "propagate": True, "handlers": []},
            "uvicorn.access": {"level": "INFO", "propagate": True, "handlers": []},
        },
    ))
"""

from prototype_highly_loaded_distributed_service_utils.logging.config import (
    build_logging_config,
)
from prototype_highly_loaded_distributed_service_utils.logging.filters import (
    ClickHouseFieldsFilter,
)

__all__ = [
    "ClickHouseFieldsFilter",
    "build_logging_config",
]
