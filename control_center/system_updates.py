"""Safe read-only system update checks and native updater discovery."""
from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable

from leos_core.json_utils import json_nesting_within_limit


MAX_RPM_OSTREE_STATUS_CHARS = 2 * 1024 * 1024
MAX_RPM_OSTREE_DEPLOYMENTS = 1000


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

    if (
        not isinstance(payload, str)
        or len(payload) > MAX_RPM_OSTREE_STATUS_CHARS
        or not json_nesting_within_limit(payload)
    ):
        return None
    try:
        status = json.loads(payload)
    except (TypeError, json.JSONDecodeError, RecursionError):
        return None
    if not isinstance(status, dict) or not isinstance(status.get("deployments"), list):
        return None
    deployments = status["deployments"]
    if len(deployments) > MAX_RPM_OSTREE_DEPLOYMENTS:
        return None
    for deployment in deployments:
        if not isinstance(deployment, dict) or deployment.get("booted") is True:
            continue
        if deployment.get("pending") is True or deployment.get("staged") is True:
            checksum = deployment.get("checksum")
            if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
                continue
            version = deployment.get("version")
            if not isinstance(version, str) or not version.strip() or len(version) > 128:
                version = "Nouvelle version"
            elif any(ord(character) < 32 or ord(character) == 127 for character in version):
                version = "Nouvelle version"
            else:
                version = version.strip()
            return {
                "checksum": checksum.lower(),
                "version": version,
            }
    return None

def deployment_inventory_from_status(payload: str) -> dict[str, str | int | bool] | None:
    """Summarize booted and retained OSTree deployments without changing them.

    The list is descriptive only: an additional deployment is not guaranteed to
    be bootable or suitable for rollback, so callers must not label it as a
    verified recovery point.
    """
    import json

    if (
        not isinstance(payload, str)
        or len(payload) > MAX_RPM_OSTREE_STATUS_CHARS
        or not json_nesting_within_limit(payload)
    ):
        return None
    try:
        status = json.loads(payload)
    except (TypeError, json.JSONDecodeError, RecursionError):
        return None
    if not isinstance(status, dict) or not isinstance(status.get("deployments"), list):
        return None

    deployments = status["deployments"]
    if not deployments or len(deployments) > MAX_RPM_OSTREE_DEPLOYMENTS:
        return None

    booted = [
        item for item in deployments
        if isinstance(item, dict) and item.get("booted") is True
    ]
    if len(booted) != 1:
        return None

    current = booted[0]
    checksum = current.get("checksum")
    if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
        return None

    version = current.get("version")
    if (
        not isinstance(version, str)
        or not version.strip()
        or len(version) > 128
        or any(ord(character) < 32 or ord(character) == 127 for character in version)
    ):
        version = "Version inconnue"
    else:
        version = version.strip()

    retained = []
    for item in deployments:
        if not isinstance(item, dict) or item.get("booted") is True:
            continue
        other_checksum = item.get("checksum")
        if (
            not isinstance(other_checksum, str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", other_checksum)
        ):
            continue
        retained.append(item)

    pending_count = sum(
        1 for item in retained
        if item.get("pending") is True or item.get("staged") is True
    )
    pinned_count = sum(1 for item in retained if item.get("pinned") is True)

    return {
        "available": True,
        "bootedVersion": version,
        "bootedChecksum": checksum.lower()[:12],
        "otherCount": len(retained),
        "pendingCount": pending_count,
        "pinnedCount": pinned_count,
    }

