"""Safe, explicit launching of locally discovered games with known Flatpak emulators.

Only a small set of unambiguous formats is mapped. The file is forwarded to
the already-installed Flatpak through the document portal; LEOS never installs
an emulator, downloads game data, or executes a ROM as a program.
"""

from __future__ import annotations

import configparser
import os
import re
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

MAX_INSTALLATION_CONFIGS = 64
MAX_INSTALLATION_CONFIG_BYTES = 32 * 1024
_INSTALLATION_SECTION = re.compile(r'^Installation "([A-Za-z0-9_-]{1,64})"$')


def _custom_flatpak_installations(config_dir: Path) -> list[tuple[Path, str]]:
    """Read bounded system Flatpak installation definitions without following symlinks."""
    if config_dir.is_symlink() or not config_dir.is_dir():
        return []

    try:
        config_files = sorted(config_dir.glob("*.conf"))[:MAX_INSTALLATION_CONFIGS]
    except OSError:
        return []

    installations: list[tuple[Path, str]] = []
    for config_file in config_files:
        try:
            if config_file.is_symlink() or not config_file.is_file():
                continue
            if config_file.stat().st_size > MAX_INSTALLATION_CONFIG_BYTES:
                continue
            content = config_file.read_text(encoding="utf-8")
            if len(content.encode("utf-8")) > MAX_INSTALLATION_CONFIG_BYTES:
                continue
            parser = configparser.ConfigParser(interpolation=None, strict=True)
            parser.read_string(content)
        except (OSError, UnicodeError, configparser.Error, ValueError):
            continue

        for section in parser.sections():
            match = _INSTALLATION_SECTION.fullmatch(section)
            if match is None:
                continue
            configured_path = parser.get(section, "Path", fallback="").strip()
            if not configured_path:
                continue
            root = Path(configured_path).expanduser()
            if not root.is_absolute() or root.is_symlink() or not root.is_dir():
                continue
            installations.append((root, match.group(1)))

    return installations


def _installed_emulator_selector(
    app_id: str,
    *,
    data_root: Path,
    system_installations_config_dir: Path,
) -> str | None | bool:
    """Return a named-installation selector, None for default installs, or False."""
    default_roots = (
        data_root / "flatpak",
        Path("/var/lib/flatpak"),
    )
    for root in default_roots:
        app_path = root / "app" / app_id
        if not root.is_symlink() and app_path.is_dir() and not app_path.is_symlink():
            return None

    for root, installation_name in _custom_flatpak_installations(
        system_installations_config_dir
    ):
        app_path = root / "app" / app_id
        if app_path.is_dir() and not app_path.is_symlink():
            return f"--installation={installation_name}"

    return False


def build_emulator_launch_command(
    game_path: str | Path,
    *,
    home: Path | None = None,
    data_home: Path | None = None,
    flatpak_executable: str | None = None,
    system_installations_config_dir: Path | None = None,
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

    config_dir = (
        Path(system_installations_config_dir)
        if system_installations_config_dir is not None
        else Path("/etc/flatpak/installations.d")
    )
    selector = _installed_emulator_selector(
        app_id,
        data_root=data_root,
        system_installations_config_dir=config_dir,
    )
    if selector is False:
        return None, f"L'émulateur requis ({app_id}) n'est pas installé."

    # Named installations must be selected explicitly so Flatpak opens the
    # existing deployment on an external/custom installation rather than
    # reporting that the app is absent from the default installation.
    prefix = [executable]
    if isinstance(selector, str):
        prefix.append(selector)

    # Flatpak's document portal grants the app access to this one selected file.
    return [
        *prefix, "run", "--file-forwarding", app_id, "@@", str(resolved), "@@"
    ], ""
