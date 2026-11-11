"""Allowlisted shortcuts to native KDE Plasma configuration modules.

Keeping this mapping in a Qt-free module makes command construction testable
without a running Plasma session. User input is never passed as an executable
or arbitrary command-line argument.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable

SETTINGS_MODULES: dict[str, str] = {
    "bluetooth": "kcm_bluetooth",
    "network": "kcm_networkmanagement",
    "audio": "kcm_pulseaudio",
    "display": "kcm_kscreen",
    "power": "kcm_powerdevilprofilesconfig",
    "keyboard": "kcm_keyboard",
    "mouse": "kcm_mouse",
}


def settings_module_command(
    section: str,
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """Return a safe launch command for a known KDE module, if available."""
    module = SETTINGS_MODULES.get(section)
    if module is None:
        return None
    executable = find_executable("kcmshell6") or find_executable("systemsettings")
    return [executable, module] if executable else None


def general_settings_command(
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """Return the command for the full KDE System Settings window."""
    executable = find_executable("systemsettings")
    return [executable] if executable else None
