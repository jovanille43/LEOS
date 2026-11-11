"""Safe integration with power-profiles-daemon.

Only queries the daemon during discovery. Changing the active profile is a
separate explicit action initiated by the user from Gaming Mode.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


PROFILE_LABELS = {
    "power-saver": "Économie d'énergie",
    "balanced": "Équilibré",
    "performance": "Performance",
}


@dataclass(frozen=True)
class PowerProfileState:
    available: bool
    active: str
    profiles: tuple[str, ...]
    message: str


def _run(command: list[str], timeout: float = 2.0) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def inspect_power_profiles() -> PowerProfileState:
    """Return only profiles actually advertised by the host daemon."""
    executable = shutil.which("powerprofilesctl")
    if not executable:
        return PowerProfileState(False, "", (), "power-profiles-daemon indisponible")
    active = _run([executable, "get"])
    raw = _run([executable, "list"])
    profiles: list[str] = []
    for line in raw.splitlines():
        candidate = line.strip().lstrip("*").strip().split()[0:1]
        if candidate and candidate[0] in PROFILE_LABELS and candidate[0] not in profiles:
            profiles.append(candidate[0])
    if not profiles and active in PROFILE_LABELS:
        profiles = [active]
    if not profiles:
        return PowerProfileState(False, active, (), "Aucun profil natif exploitable détecté")
    if active not in profiles:
        active = ""
    return PowerProfileState(True, active, tuple(profiles), "Profils natifs disponibles")


def set_power_profile(profile: str) -> tuple[bool, str]:
    """Apply a daemon profile; callers must obtain explicit user confirmation."""
    if profile not in PROFILE_LABELS:
        return False, "Profil non reconnu"
    state = inspect_power_profiles()
    if not state.available or profile not in state.profiles:
        return False, "Ce profil n'est pas proposé par le système"
    executable = shutil.which("powerprofilesctl")
    if not executable:
        return False, "power-profiles-daemon indisponible"
    try:
        result = subprocess.run(
            [executable, "set", profile],
            capture_output=True,
            text=True,
            check=False,
            timeout=4.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "Impossible de contacter le service de gestion d'énergie"
    if result.returncode != 0:
        return False, (result.stderr or "Le système a refusé le changement de profil").strip()
    return True, f"Profil actif : {PROFILE_LABELS[profile]}"
