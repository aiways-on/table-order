"""Structured JSON logging with correlation id + sensitive-data masking.  [SEC-03][RES-05]"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

# Keys whose values must never be logged in the clear. [SEC-03]
_SENSITIVE_KEYS = {
    "password",
    "admin_password",
    "password_hash",
    "admin_password_hash",
    "table_password_hash",
    "token",
    "session_token",
    "jwt",
    "jwt_secret",
    "authorization",
    "secret",
}
_MASK = "***"


def mask_sensitive(data: Any) -> Any:
    """Recursively mask sensitive keys in dict/list structures."""
    if isinstance(data, dict):
        return {
            k: (_MASK if k.lower() in _SENSITIVE_KEYS else mask_sensitive(v))
            for k, v in data.items()
        }
    if isinstance(data, (list, tuple)):
        return [mask_sensitive(v) for v in data]
    return data


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Lazily import to avoid a cycle at module load.
        from app.core.context import get_context

        ctx = get_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": ctx.correlation_id,
        }
        extra = getattr(record, "context", None)
        if extra:
            payload["context"] = mask_sensitive(extra)
        return json.dumps(payload, default=str)


class _StructuredLogger:
    """Thin wrapper giving structlog-style `logger.info("msg", key=val)` ergonomics."""

    def __init__(self, name: str):
        self._log = logging.getLogger(name)

    def _emit(self, level: int, message: str, **context: Any) -> None:
        self._log.log(level, message, extra={"context": context or None})

    def debug(self, message: str, **c: Any) -> None:
        self._emit(logging.DEBUG, message, **c)

    def info(self, message: str, **c: Any) -> None:
        self._emit(logging.INFO, message, **c)

    def warning(self, message: str, **c: Any) -> None:
        self._emit(logging.WARNING, message, **c)

    def error(self, message: str, **c: Any) -> None:
        self._emit(logging.ERROR, message, **c)

    def security(self, message: str, **c: Any) -> None:
        """Security-level event marker.  [SEC-14]"""
        self._emit(logging.WARNING, f"SECURITY {message}", security_event=True, **c)


_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(get_settings().log_level.upper())
    _configured = True


def get_logger(name: str) -> _StructuredLogger:
    return _StructuredLogger(name)
