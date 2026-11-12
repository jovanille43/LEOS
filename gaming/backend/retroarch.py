"""Read-only import of RetroArch JSON playlists.

The importer never scans ROM folders or downloads content. It reads the user's
existing .lpl playlists and builds argument arrays for the installed launcher.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from leos_core.text import normalize_search_text


RETROARCH_FLATPAK_ID = "org.libretro.RetroArch"
MAX_PLAYLIST_BYTES = 16 * 1024 * 1024
MAX_PLAYLIST_ITEMS = 20_000
_IGNORED_PLAYLISTS = {"content_favorites", "content_history", "favorites", "history"}


def find_retroarch_playlist_directories(
    home: Path | None = None,
    xdg_config_home: Path | None = None,
) -> list[Path]:
    """Find default and explicitly configured local playlist directories."""
    home = Path.home() if home is None else Path(home).expanduser()
    if xdg_config_home is None or not Path(xdg_config_home).expanduser().is_absolute():
        config_home = home / ".config"
    else:
        config_home = Path(xdg_config_home).expanduser()

    config_roots = [
        config_home / "retroarch",
        home / ".config" / "retroarch",
        home / ".var/app/org.libretro.RetroArch/config/retroarch",
    ]
    directories: list[Path] = []
    seen: set[str] = set()

    def add_directory(candidate: Path) -> None:
        try:
            if not candidate.is_dir():
                return
            resolved = candidate.resolve()
            key = str(resolved)
            if key not in seen:
                seen.add(key)
                directories.append(resolved)
        except (OSError, RuntimeError):
            return

    for root in config_roots:
        add_directory(root / "playlists")
        try:
            config = (root / "retroarch.cfg").read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            continue
        match = re.search(
            r'^\\s*playlist_directory\\s*=\\s*"([^"]+)"',
            config,
            re.MULTILINE,
        )
        if match and match.group(1).casefold() != "default":
            configured = Path(match.group(1)).expanduser()
            if configured.is_absolute():
                add_directory(configured)

    return directories


def _local_content_path(raw_path: Any, base_directory: Any = "") -> str:
    """Resolve a local content path, including RetroArch's archive#member form."""
    if not isinstance(raw_path, str):
        return ""
    value = raw_path.strip()
    if (
        not value
        or "\x00" in value
        or "://" in value
        or value.startswith("//")
        or "\\" in value
        or re.match(r"^[A-Za-z]:[/\\]", value)
    ):
        return ""

    archive_path, separator, member = value.partition("#")
    candidate = Path(archive_path).expanduser()
    if not candidate.is_absolute():
        if not isinstance(base_directory, str) or not base_directory.strip():
            return ""
        base = Path(base_directory.strip()).expanduser()
        if not base.is_absolute():
            return ""
        candidate = base / candidate
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError):
        return ""
    result = str(resolved)
    if separator:
        if not member or "\x00" in member:
            return ""
        result += "#" + member
    return result


def _system_category(database_name: str, playlist_name: str) -> str:
    value = normalize_search_text(f"{database_name} {playlist_name}")
    if any(token in value for token in (
        "mame", "fbneo", "finalburn", "arcade", "neo geo", "neogeo",
        "fba", "cps1", "cps2", "cps3",
    )):
        return "Arcade"
    if any(token in value for token in (
        "nintendo", "game boy", "gameboy", "gamecube", "wii", "switch",
        "famicom", "super nintendo", "nes", "snes", "gba", "gbc", "nds",
        "3ds", "virtual boy",
    )):
        return "Nintendo"
    if any(token in value for token in (
        "playstation", "sony", "psx", "ps1", "ps2", "ps3", "psp", "ps vita",
        "psvita",
    )):
        return "PlayStation"
    if any(token in value for token in (
        "sega", "mega drive", "megadrive", "genesis", "master system",
        "game gear", "saturn", "dreamcast", "32x", "mega cd", "mega-cd",
    )):
        return "SEGA"
    return "RetroArch"


def _core_for_launch(core_path: Any, *, flatpak: bool) -> str:
    if not isinstance(core_path, str):
        return ""
    value = core_path.strip()
    if not value or value.upper() == "DETECT" or "\x00" in value:
        return ""
    path = Path(value).expanduser()
    if not path.is_absolute():
        return ""
    if flatpak and (value.startswith("/app/") or value.startswith("/usr/")):
        # These are paths inside the Flatpak runtime, not host filesystem paths.
        return value
    try:
        return str(path.resolve(strict=True)) if path.is_file() else ""
    except (OSError, RuntimeError):
        return ""


def _build_launch(
    content_path: str,
    core_path: Any,
    *,
    native_executable: str | None,
    flatpak_available: bool,
) -> list[str]:
    archive_path = content_path.partition("#")[0]
    content_file = Path(archive_path)
    core = _core_for_launch(
        core_path,
        flatpak=flatpak_available and not bool(native_executable),
    )
    if native_executable:
        command = [native_executable]
        if core:
            command.extend(["-L", core])
        command.append(content_path)
        return command

    if flatpak_available:
        command = ["flatpak", "run"]
        permissions: list[str] = []
        try:
            content_parent = content_file.parent.resolve(strict=True)
            if content_parent.is_dir():
                permissions.append(str(content_parent) + ":ro")
        except (OSError, RuntimeError):
            pass

        core_value = str(core_path).strip() if isinstance(core_path, str) else ""
        if core and not core_value.startswith(("/app/", "/usr/")):
            try:
                core_parent = Path(core).parent.resolve(strict=True)
                if core_parent.is_dir():
                    permissions.append(str(core_parent) + ":ro")
            except (OSError, RuntimeError):
                pass

        for permission in dict.fromkeys(permissions):
            command.append(f"--filesystem={permission}")
        command.append(RETROARCH_FLATPAK_ID)
        if core:
            command.extend(["-L", core])
        command.append(content_path)
        return command

    # Keep imported entries visible even if the user later removes RetroArch;
    # the regular launcher check will provide a precise missing-executable error.
    command = ["retroarch"]
    if core:
        command.extend(["-L", core])
    command.append(content_path)
    return command


def load_retroarch_games(
    playlist_path: Path,
    *,
    native_executable: str | None = "retroarch",
    flatpak_available: bool = False,
) -> list[dict[str, Any]]:
    """Read a RetroArch .lpl JSON playlist without modifying it."""
    if (
        playlist_path.suffix.casefold() != ".lpl"
        or playlist_path.stem.casefold() in _IGNORED_PLAYLISTS
        or not playlist_path.is_file()
    ):
        return []
    try:
        if playlist_path.stat().st_size > MAX_PLAYLIST_BYTES:
            return []
        payload = json.loads(playlist_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return []
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        return []

    default_core = payload.get("default_core_path", "")
    base_directory = payload.get("base_content_directory", "")
    playlist_name = playlist_path.stem.replace("_", " ").strip()
    games: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in payload["items"][:MAX_PLAYLIST_ITEMS]:
        if not isinstance(item, dict):
            continue
        content_path = _local_content_path(item.get("path"), base_directory)
        title = item.get("label")
        if not content_path or not isinstance(title, str) or not title.strip():
            continue
        title = title.strip()[:240]
        item_core = item.get("core_path", "")
        if not isinstance(item_core, str) or not item_core.strip() or item_core.upper() == "DETECT":
            item_core = default_core
        core_path = item_core if isinstance(item_core, str) else ""
        core_name = item.get("core_name", "")
        if not isinstance(core_name, str) or not core_name.strip() or core_name.upper() == "DETECT":
            core_name = payload.get("default_core_name", "")
        if not isinstance(core_name, str):
            core_name = ""

        identity = hashlib.sha256(
            (playlist_path.name.casefold() + "\0" + content_path).encode("utf-8")
        ).hexdigest()[:20]
        game_id = f"retroarch:{identity}"
        if game_id in seen:
            continue
        seen.add(game_id)

        database_name = item.get("db_name")
        if not isinstance(database_name, str):
            database_name = ""
        system_name = Path(database_name).stem if database_name else playlist_name
        category = _system_category(system_name, playlist_name)
        source_name = core_name.strip() or system_name
        games.append({
            "id": game_id,
            "title": title,
            "platform": category,
            "source": f"RetroArch · {source_name}",
            "app_id": system_name[:120],
            "content_path": content_path,
            "core_name": core_name.strip(),
            "launch": _build_launch(
                content_path,
                core_path,
                native_executable=native_executable,
                flatpak_available=flatpak_available and not native_executable,
            ),
            "artwork": "",
        })
    return games
