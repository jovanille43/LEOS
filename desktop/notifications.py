"""Small API for components that emit LEOS-owned notifications."""
from __future__ import annotations

import shutil
import subprocess

from desktop.notification_store import NotificationStore


def _show_native_notification(title: str, body: str, level: str) -> None:
    """Forward desktop notifications to the active freedesktop notification service."""
    executable = shutil.which("notify-send")
    if not executable:
        return
    urgency = {"info": "normal", "success": "low", "warning": "normal", "error": "critical"}[level]
    command = [
        executable, "--app-name=LEOS", "--icon=leos",
        f"--urgency={urgency}", "--expire-time=5000", "--", title,
    ]
    if body:
        command.append(body)
    try:
        subprocess.run(
            command, check=False, timeout=2,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def post_notification(
    title: str,
    body: str = "",
    level: str = "info",
    *,
    native: bool = True,
) -> str | None:
    """Persist a LEOS event and optionally show a native desktop notice."""
    try:
        identifier = NotificationStore().add(title, body, level)
    except (OSError, ValueError):
        return None
    if native:
        _show_native_notification(title.strip(), body, level)
    return identifier
