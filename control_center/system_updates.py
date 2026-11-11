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


def rpm_ostree_status_command(
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """Return a read-only query for current and pending deployments."""
    executable = find_executable("rpm-ostree")
    return [executable, "status", "--json"] if executable else None


def pending_deployment_from_status(payload: str) -> dict[str, str] | None:
    """Extract an actually staged/pending deployment from rpm-ostree JSON."""
    import json

    try:
        status = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(status, dict) or not isinstance(status.get("deployments"), list):
        return None
    for deployment in status["deployments"]:
        if not isinstance(deployment, dict) or deployment.get("booted") is True:
            continue
        if deployment.get("pending") is True or deployment.get("staged") is True:
            checksum = deployment.get("checksum")
            if not isinstance(checksum, str) or not checksum:
                continue
            version = deployment.get("version")
            return {
                "checksum": checksum,
                "version": version if isinstance(version, str) and version else "Nouvelle version",
            }
    return None
