"""Read-only checks for emulator setup prerequisites.

Only inspect small, well-known configuration locations. Never read BIOS,
firmware, keys, ROM contents, or upload user files.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tomllib
from pathlib import Path
from typing import Any


MAX_CONFIG_BYTES = 128 * 1024
MAX_DIRECTORY_ENTRIES = 512
MAX_RETROARCH_CORES = 256
MELONDS_BIOS_SIZES = {
    "bios9.bin": {4 * 1024},
    "bios7.bin": {16 * 1024},
    "firmware.bin": {128 * 1024, 256 * 1024, 512 * 1024},
}


def _is_regular_file(path: Path, expected_sizes: set[int] | None = None) -> bool:
    try:
        if path.is_symlink():
            return False
        metadata = path.stat(follow_symlinks=False)
    except OSError:
        return False
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size <= 0:
        return False
    return expected_sizes is None or metadata.st_size in expected_sizes


def _is_directory(path: Path) -> bool:
    try:
        return not path.is_symlink() and path.is_dir()
    except OSError:
        return False


def _flatpak_config_root(home: Path, app_id: str) -> Path:
    return home / ".var" / "app" / app_id / "config"


def _pcsx2_status(home: Path, config_home: Path) -> str:
    candidates = (
        _flatpak_config_root(home, "net.pcsx2.PCSX2") / "PCSX2" / "bios",
        config_home / "PCSX2" / "bios",
    )
    for directory in candidates:
        if not _is_directory(directory):
            continue
        try:
            with os.scandir(directory) as entries:
                for index, entry in enumerate(entries):
                    if index >= MAX_DIRECTORY_ENTRIES:
                        break
                    if (
                        entry.name.casefold().endswith(".bin")
                        and entry.is_file(follow_symlinks=False)
                        and _is_regular_file(Path(entry.path))
                    ):
                        return (
                            "PCSX2 · fichier BIOS détecté — vérification finale à "
                            "faire dans PCSX2"
                        )
        except OSError:
            continue
    return "PCSX2 · BIOS PS2 à ajouter dans le dossier de configuration"


def _toml_config(path: Path) -> dict[str, Any]:
    try:
        if not _is_regular_file(path):
            return {}
        if path.stat(follow_symlinks=False).st_size > MAX_CONFIG_BYTES:
            return {}
        raw = path.read_text(encoding="utf-8")
        parsed = tomllib.loads(raw)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _configured_path(
    data_directory: Path,
    configured_value: Any,
    default_name: str,
) -> Path:
    if isinstance(configured_value, str) and configured_value and len(configured_value) <= 4096:
        if "\x00" not in configured_value:
            candidate = Path(configured_value).expanduser()
            return candidate if candidate.is_absolute() else data_directory / candidate
    return data_directory / default_name


def _melonds_status(home: Path, config_home: Path) -> str:
    directories = (
        _flatpak_config_root(home, "net.kuribo64.melonDS") / "melonDS",
        config_home / "melonDS",
    )
    for directory in directories:
        if not _is_directory(directory):
            continue
        settings = _toml_config(directory / "melonDS.toml")
        ds = settings.get("DS", {})
        if not isinstance(ds, dict):
            ds = {}
        paths = {
            name: _configured_path(directory, ds.get(key), name)
            for name, key in (
                ("bios9.bin", "BIOS9Path"),
                ("bios7.bin", "BIOS7Path"),
                ("firmware.bin", "FirmwarePath"),
            )
        }
        present = sum(
            _is_regular_file(paths[name], sizes)
            for name, sizes in MELONDS_BIOS_SIZES.items()
        )
        if present == 3:
            return (
                "melonDS · BIOS et firmware DS détectés — vérification finale "
                "à faire dans melonDS"
            )
        if present:
            return f"melonDS · prérequis DS incomplets ({present}/3 fichiers détectés)"
        return "melonDS · BIOS et firmware DS à configurer"
    return "melonDS · BIOS et firmware DS à configurer"


def _rpcs3_status(home: Path, config_home: Path) -> str:
    candidates = (
        _flatpak_config_root(home, "net.rpcs3.RPCS3") / "rpcs3" / "dev_flash",
        config_home / "rpcs3" / "dev_flash",
    )
    for dev_flash in candidates:
        if not _is_directory(dev_flash):
            continue
        if _is_regular_file(dev_flash / "sys" / "external" / "liblv2.sprx"):
            return (
                "RPCS3 · module firmware PS3 détecté — lancement de test "
                "encore nécessaire"
            )
    return "RPCS3 · firmware PS3 à installer depuis le menu Fichier de RPCS3"


def _retroarch_config_directories(home: Path, config_home: Path) -> list[Path]:
    return [
        _flatpak_config_root(home, "org.libretro.RetroArch") / "retroarch",
        config_home / "retroarch",
    ]


def _retroarch_core_directory(config_directory: Path) -> Path:
    config_file = config_directory / "retroarch.cfg"
    if _is_regular_file(config_file):
        try:
            if config_file.stat(follow_symlinks=False).st_size <= MAX_CONFIG_BYTES:
                lines = config_file.read_text(encoding="utf-8").splitlines()
            else:
                lines = []
        except (OSError, UnicodeError):
            lines = []
        for line in lines[:4096]:
            match = re.match(r'^\s*libretro_directory\s*=\s*(".*")\s*(?:#.*)?$', line)
            if not match:
                continue
            try:
                value = json.loads(match.group(1))
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(value, str) and value and len(value) <= 4096 and "\x00" not in value:
                configured = Path(value).expanduser()
                return configured if configured.is_absolute() else config_directory / configured
    return config_directory / "cores"


def _count_retroarch_cores(directory: Path) -> int:
    if not _is_directory(directory):
        return 0
    count = 0
    try:
        with os.scandir(directory) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_DIRECTORY_ENTRIES:
                    break
                if count >= MAX_RETROARCH_CORES:
                    break
                if (
                    entry.name.endswith(".so")
                    and entry.is_file(follow_symlinks=False)
                    and _is_regular_file(Path(entry.path))
                ):
                    count += 1
    except OSError:
        return 0
    return count


def _retroarch_status(home: Path, config_home: Path) -> str:
    core_count = 0
    for config_directory in _retroarch_config_directories(home, config_home):
        core_count = max(
            core_count,
            _count_retroarch_cores(_retroarch_core_directory(config_directory)),
        )
    if core_count:
        return f"RetroArch · {core_count} cœur(s) détecté(s)"
    return "RetroArch · aucun cœur détecté — choisir les systèmes dans RetroArch"


def detect_emulator_prerequisite_statuses(
    *,
    home: Path | None = None,
    config_home: Path | None = None,
) -> list[str]:
    """Return short, read-only prerequisite statuses for the Gaming quick panel.

    File presence and directory layout are hints only: they do not validate
    firmware authenticity, correctness, compatibility, or successful boot.
    """
    home = Path(home) if home is not None else Path.home()
    config_home = Path(config_home) if config_home is not None else home / ".config"
    return [
        _pcsx2_status(home, config_home),
        _melonds_status(home, config_home),
        _rpcs3_status(home, config_home),
        _retroarch_status(home, config_home),
        "Dolphin / PPSSPP · aucun BIOS séparé requis pour un lancement standard",
    ]
