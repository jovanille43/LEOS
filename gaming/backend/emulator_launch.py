"""Safe, explicit launching of locally discovered games with known Flatpak emulators.

Only a small set of unambiguous formats is mapped. The file is forwarded to
the already-installed Flatpak through the document portal; LEOS never installs
an emulator, downloads game data, or executes a ROM as a program.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .emulation_discovery import default_scan_roots, MAX_PATH_LENGTH


EMULATOR_BY_EXTENSION: dict[str, str] = {
    # GameCube / Wii
    ".gcm": "org.DolphinEmu.dolphin-emu",
    ".wbfs": "org.DolphinEmu.dolphin-emu",
    ".rvz": "org.DolphinEmu.dolphin-emu",
    # Wii U
    ".wua": "info.cemu.Cemu",
    ".wuhb": "info.cemu.Cemu",
    ".wud": "info.cemu.Cemu",
    ".wux": "info.cemu.Cemu",
    # Nintendo Switch 1
    ".nsp": "dev.eden_emu.eden",
    ".xci": "dev.eden_emu.eden",
    # PSP formats that do not overlap with PlayStation 1
    ".cso": "org.ppsspp.PPSSPP",
    ".zso": "org.ppsspp.PPSSPP",
}


def build_emulator_launch_command(
    game_path: str | Path,
    *,
    home: Path | None = None,
    data_home: Path | None = None,
    flatpak_executable: str | None = None,
) -> tuple[list[str] | None, str]:
    """Return a Flatpak document-portal launch command or a safe French error."""
    if not isinstance(game_path, (str, Path)):
        return None, "Chemin du jeu invalide."
    raw_path = str(game_path)
    if not raw_path or len(raw_path) > MAX_PATH_LENGTH or chr(0) in raw_path:
        return None, "Chemin du jeu invalide."

    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute() or candidate.is_symlink():
        return None, "Le fichier du jeu n'est pas un fichier local sûr."

    base = Path(home or Path.home()).expanduser().resolve()
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_file():
            return None, "Le fichier du jeu est introuvable."
        allowed = False
        for root_candidate in default_scan_roots(base):
            if root_candidate.is_symlink() or not root_candidate.is_dir():
                continue
            root = root_candidate.resolve(strict=True)
            try:
                resolved.relative_to(root)
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            return None, "Le jeu doit se trouver dans un dossier de bibliothèque LEOS."
    except (OSError, RuntimeError, ValueError):
        return None, "Le fichier du jeu est introuvable ou inaccessible."

    app_id = EMULATOR_BY_EXTENSION.get(resolved.suffix.casefold())
    if not app_id:
        return None, "Aucun émulateur automatique fiable pour ce format ; ajoute-le manuellement."
    executable = flatpak_executable or shutil.which("flatpak")
    if not executable:
        return None, "Flatpak n'est pas disponible sur ce système."

    if data_home is None:
        configured = os.environ.get("XDG_DATA_HOME", "")
        data_root = Path(configured).expanduser() if configured else base / ".local/share"
    else:
        data_root = Path(data_home).expanduser()
    if not data_root.is_absolute():
        data_root = base / ".local/share"
    installed_roots = (data_root / "flatpak/app", Path("/var/lib/flatpak/app"))
    if not any((root / app_id).is_dir() for root in installed_roots):
        return None, f"L'émulateur requis ({app_id}) n'est pas installé."

    # Flatpak's document portal grants the app access to this one selected file.
    return [
        executable, "run", "--file-forwarding", app_id, "@@", str(resolved), "@@"
    ], ""
