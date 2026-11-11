"""Safe read-only system update checks and native updater discovery."""
from __future__ import annotations

import os
import shutil
from collections.abc import Callable


def system_update_check_command(
    find_executable: Callable[[str], str | None] = shutil.which,
    effective_uid: Callable[[], int] = os.geteuid,
) -> list[str] | None:
    """Build the uupd check-only command; never start an update operation."""
    uupd = find_executable("uupd")
    if not uupd:
        return None
    if effective_uid() == 0:
        return [uupd, "update-check"]
    polkit = find_executable("pkexec")
    if not polkit:
        return None
    return [polkit, uupd, "update-check"]


def system_updater_command(
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """Return the official Bazzite Updater launcher when installed."""
    updater = find_executable("bazzite-updater")
    return [updater] if updater else None


def interpret_update_check_exit_code(exit_code: int) -> str:
    """Map uupd update-check exit codes to stable LEOS status keys."""
    if exit_code == 0:
        return "available"
    if exit_code == 77:
        return "up_to_date"
    if exit_code in {126, 127}:
        return "cancelled"
    return "error"
