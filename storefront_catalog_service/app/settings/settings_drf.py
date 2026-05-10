from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
from typing import Any

from rest_framework.parsers import BaseParser
from rest_framework.renderers import BaseRenderer

import orjson

# ---------------------------------------------------------------------------
# orjson-backed renderer / parser
# ---------------------------------------------------------------------------
#
# Why orjson:
#   * 2-5x faster encode, ~2x faster decode vs stdlib `json` on realistic DRF
#     payloads (lists of dicts with str/int/float/datetime/UUID).
#   * Native UUID, datetime, dataclass support - no custom encoder needed.
#   * Always emits valid UTF-8 bytes; we skip the str round-trip that DRF's
#     default JSONRenderer does.
#
# Notes on options:
#   * OPT_NON_STR_KEYS — DRF occasionally produces dicts keyed by int (e.g.
#     ChoiceField with int choices in error payloads). Without this, orjson
#     would raise TypeError.
#   * OPT_SERIALIZE_NUMPY — cheap to enable; future-proofs against analytics
#     endpoints that might return numpy arrays.
#   * Datetime format: orjson emits ``...Z`` for UTC. DRF default emits
#     ``...+00:00``. Both are valid ISO-8601; ``Z`` is shorter and parses
#     everywhere modern (browsers, mobile, Go, Java). Not enabling
#     OPT_UTC_Z explicitly because orjson uses it by default for UTC.
#   * `default=_orjson_default` - fallback for types orjson doesn't handle
#     natively. Decimal is the main one (DRF's DecimalField returns Decimal
#     when `coerce_to_string=False`; we stringify to preserve precision).


_ORJSON_OPTS = orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY


def _orjson_default(obj: Any) -> Any:
    """Fallback encoder for types orjson can't serialize natively."""
    if isinstance(obj, Decimal):
        # Stringify to preserve full precision - float would silently round.
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class ORJSONRenderer(BaseRenderer):
    """
    DRF renderer backed by orjson.

    Drop-in replacement for ``rest_framework.renderers.JSONRenderer``.
    Returns raw bytes (DRF accepts bytes from renderers - no decode needed).
    """

    media_type = "application/json"
    format = "json"
    charset = None  # bytes, not str - DRF will not re-encode
    render_style = "binary"

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: Mapping[str, Any] | None = None,
    ) -> bytes:
        if data is None:
            return b""
        return orjson.dumps(data, default=_orjson_default, option=_ORJSON_OPTS)


class ORJSONParser(BaseParser):
    """
    DRF parser backed by orjson.

    Drop-in replacement for ``rest_framework.parsers.JSONParser``.
    """

    media_type = "application/json"

    def parse(
        self,
        stream: Any,
        media_type: str | None = None,
        parser_context: Mapping[str, Any] | None = None,
    ) -> Any:
        try:
            return orjson.loads(stream.read())
        except orjson.JSONDecodeError as exc:
            # DRF expects ParseError; import locally to keep module-import
            # surface small.
            from rest_framework.exceptions import ParseError

            raise ParseError(f"JSON parse error - {exc}") from exc


# ---------------------------------------------------------------------------
# DRF settings
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "settings.settings_drf.ORJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "settings.settings_drf.ORJSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Storefront Catalog API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Authentication", "description": "Password-based JWT authentication"},
        {"name": "OTP Authentication", "description": "Passwordless OTP-based authentication (2FA)"},
        {"name": "User", "description": "User management endpoints"},
    ],
    "OPERATION_SORTER": "alpha",
}
