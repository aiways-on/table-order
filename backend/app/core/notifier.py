"""Security-event notification adapter.  [SEC-14][RES-15]

Interface + default log-based implementation. Real channels (webhook/email/Slack)
can be plugged in later without touching call sites.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger

logger = get_logger("security")


class Notifier(ABC):
    @abstractmethod
    def notify_security_event(self, event: str, **context: Any) -> None:
        ...


class LogNotifier(Notifier):
    """Default implementation: records the event at SECURITY level."""

    def notify_security_event(self, event: str, **context: Any) -> None:
        logger.security(event, **context)


_notifier: Notifier = LogNotifier()


def get_notifier() -> Notifier:
    return _notifier


def set_notifier(notifier: Notifier) -> None:
    """Swap the adapter (e.g., to a webhook implementation)."""
    global _notifier
    _notifier = notifier
