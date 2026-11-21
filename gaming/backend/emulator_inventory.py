"""Read-only discovery of optional emulator installations for Gaming Mode.

Detection deliberately checks known executable names and deployed Flatpak refs.
It never installs applications, opens user data folders, or scans ROM files.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable


EMULATORS = (
    {
        "id": "org.libretro.RetroArch",
        "name": "RETROARCH",
        "binaries": ("retroarch",),
    },
    {
        "id": "org.DolphinEmu.dolphin-emu",
        "name": "DOLPHIN",
        "binaries": ("dolphin-emu", "dolphin"),
    },
    {
        "id": "net.pcsx2.PCSX2",
        "name": "PCSX2",
        "binaries": ("pcsx2-qt", "pcsx2"),
    },
    {
        "id": "org.ppsspp.PPSSPP",
        "name": "PPSSPP",
        "binaries": ("PPSSPPQt", "ppsspp"),
    },
    {
        "id": "net.kuribo64.melonDS",
        "name": "MELONDS",
        "binaries": ("melonDS", "melonds"),
    },
    {
        "id": "net.rpcs3.RPCS3",
        "name": "RPCS3",
        "binaries": ("rpcs3",),
    },
    {
        "id": "dev.eden_emu.eden",
        "name": "EDEN",
        "binaries": ("eden", "eden-launcher"),
    },
)

SYSTEM_FLATPAK_APP_ROOT = Path("/var/lib/flatpak/app")


def _flatpak_ref_is_deployed(app_root: Path) -> bool:
    """Return true only when an app has an architecture/branch deployment path."""
    try:
        if app_root.is_symlink() or not app_root.is_dir():
            return False
        for architecture in app_root.iterdir():
            if architecture.is_symlink() or not architecture.is_dir():
                continue
            for branch in architecture.iterdir():
                if not branch.is_dir():
                    continue
                # A deployed Flatpak app contains a deployment directory with
                # its files/ tree (including the active deployment symlink).
                for deployment in branch.iterdir():
                    if deployment.is_dir() and (deployment / "files").is_dir():
                        return True
    except OSError:
        return False
    return False


def detect_emulator_installations(
    *,
    which: Callable[[str], str | None] | None = None,
    data_home: Path | None = None,
    system_flatpak_root: Path = SYSTEM_FLATPAK_APP_ROOT,
) -> list[dict[str, str]]:
    """Return the curated emulator status without invoking package managers.

    Native binaries take precedence over Flatpak when both are present.
    User Flatpak deployments are searched in XDG_DATA_HOME; system deployments
    are searched in the standard system Flatpak app root.
    """
    which = shutil.which if which is None else which
    data_home = Path(data_home) if data_home is not None else Path.home() / ".local/share"
    roots = (
        ("UTILISATEUR", data_home / "flatpak/app"),
        ("SYSTÈME", Path(system_flatpak_root)),
    )

    results: list[dict[str, str]] = []
    for emulator in EMULATORS:
        executable = next(
            (path for binary in emulator["binaries"] if (path := which(binary))),
            "",
        )
        scope = "NATIF" if executable else ""
        if not scope:
            for flatpak_scope, root in roots:
                if _flatpak_ref_is_deployed(root / emulator["id"]):
                    scope = f"FLATPAK {flatpak_scope}"
                    break
        results.append({
            "id": emulator["id"],
            "name": emulator["name"],
            "scope": scope,
            "status": (
                f"{emulator['name']} · DISPONIBLE ({scope})"
                if scope else f"{emulator['name']} · NON DÉTECTÉ"
            ),
        })
    return results



def build_emulator_frontend_command(
    app_id: str,
    *,
    which: Callable[[str], str | None] | None = None,
    data_home: Path | None = None,
    system_flatpak_root: Path = SYSTEM_FLATPAK_APP_ROOT,
) -> list[str]:
    """Return a safe argv to open a known, already-installed emulator frontend.

    Native executables take precedence. Flatpak is invoked only when the
    requested app has a real user or system deployment; this helper never
    installs software, grants filesystem permissions, or accepts free-form
    commands from the interface.
    """
    emulator = next((item for item in EMULATORS if item["id"] == app_id), None)
    if emulator is None:
        return []

    which = shutil.which if which is None else which
    data_home = Path(data_home) if data_home is not None else Path.home() / ".local/share"
    native = next(
        (path for binary in emulator["binaries"] if (path := which(binary))),
        None,
    )
    if native:
        return [native]

    flatpak = which("flatpak")
    if not flatpak:
        return []

    user_root = data_home / "flatpak" / "app"
    if _flatpak_ref_is_deployed(user_root / app_id):
        return [flatpak, "run", app_id]
    if _flatpak_ref_is_deployed(Path(system_flatpak_root) / app_id):
        return [flatpak, "run", app_id]
    return []
