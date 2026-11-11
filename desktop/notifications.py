"""Small API for components that emit LEOS-owned notifications."""
from __future__ import annotations

from desktop.notification_store import NotificationStore


def post_notification(title: str, body: str = "", level: str = "info") -> str | None:
    """Persist one notification; UI activity must never fail because history is unavailable."""
    try:
        return NotificationStore().add(title, body, level)
    except (OSError, ValueError):
        return None
