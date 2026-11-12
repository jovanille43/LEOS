"""Small API for components that emit LEOS-owned notifications."""
from __future__ import annotations

import shutil
import subprocess

from desktop.notification_store import NotificationStore
from leos_core.settings import SettingsStore


_PRIORITY = {"info": 0, "success": 0, "warning": 1, "error": 2}
_MINIMUM_PRIORITY = {"all": 0, "important": 1, "critical": 2}


def _show_native_notification(title: str, body: str, level: str) -> None:
    """Forward eligible notices to the active freedesktop notification service."""
    settings = SettingsStore()
    (
        enabled,
        minimum,
        last_mode,
        silent_in_gaming,
        duration,
        sounds_enabled,
    ) = settings.snapshot((
        "notifications_enabled",
        "notification_minimum_priority",
        "last_mode",
        "silent_notifications_in_gaming",
        "notification_duration_seconds",
        "notification_sounds_enabled",
    ))
    if not enabled:
        return
    if _PRIORITY[level] < _MINIMUM_PRIORITY.get(minimum, 0):
        return
    if last_mode == "gaming" and silent_in_gaming:
        return

    executable = shutil.which("notify-send")
    if not executable:
        return
    urgency = {"info": "normal", "success": "low", "warning": "normal", "error": "critical"}[level]
    command = [
        executable, "--app-name=LEOS", "--icon=leos",
        f"--urgency={urgency}", f"--expire-time={duration * 1000}",
    ]
    if not sounds_enabled:
        command.append("--hint=boolean:suppress-sound:true")
    command.extend(["--", title])
    if body:
        command.append(body)
    try:
        # Notifications are best-effort UI feedback. Spawn notify-send without
        # waiting so a slow desktop bus cannot stall Gaming or Desktop.
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except OSError:
        return


def post_notification(
    title: str,
    body: str = "",
    level: str = "info",
    *,
    native: bool = True,
) -> str | None:
    """Persist every LEOS event; user preferences govern only native popups."""
    try:
        identifier = NotificationStore().add(title, body, level)
    except (OSError, ValueError):
        return None
    if native:
        _show_native_notification(title.strip(), body, level)
    return identifier
