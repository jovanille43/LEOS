"""Safe discovery and last-seen cache for Steam library folders.

Only Steam's own libraryfolders.vdf and appmanifest metadata are read. The
cache stores minimal game metadata so titles on a disconnected secondary
library remain visible; no game files or content are copied or modified.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable

from .library_state import read_bounded_json, read_bounded_text, write_bounded_json


MAX_STEAM_LIBRARY_LOCATIONS = 32
MAX_STEAM_CACHE_GAMES = 20_000
MAX_STEAM_CACHE_BYTES = 8 * 1024 * 1024
MAX_STEAM_LIBRARY_PATH_LENGTH = 4096
MAX_STEAM_TITLE_LENGTH = 256
_STEAM_APP_ID = re.compile(r"^[0-9]{1,12}$")
_STEAM_PATH_FIELD = re.compile(r'"path"\s+"((?:\\.|[^"\\])*)"', re.IGNORECASE)


def _normal_absolute_path(raw_value: str) -> Path | None:
    if (
        not isinstance(raw_value, str)
        or not raw_value
        or len(raw_value) > MAX_STEAM_LIBRARY_PATH_LENGTH
        or "\x00" in raw_value
    ):
        return None
    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        return None
    normalized = Path(os.path.normpath(str(candidate)))
    if normalized == Path("/"):
        return None
    return normalized


def steam_library_locations(default_roots: Iterable[Path]) -> list[Path]:
    """Return deduplicated declared Steam library roots, including offline paths.

    A root from libraryfolders.vdf is retained even when it is not mounted. This
    lets the caller distinguish a disconnected secondary library from an
    uninstalled game, while actual manifest scans are performed only on
    existing, non-symlinked steamapps directories.
    """
    locations: list[Path] = []
    seen: set[str] = set()

    def add(candidate: Path) -> None:
        if len(locations) >= MAX_STEAM_LIBRARY_LOCATIONS:
            return
        try:
            if candidate.is_symlink():
                return
            root = candidate.resolve(strict=True) if candidate.exists() else candidate
            if not root.is_absolute() or root == Path("/"):
                return
            key = os.path.normpath(str(root))
            if key in seen:
                return
            seen.add(key)
            locations.append(Path(key))
        except (OSError, RuntimeError, ValueError):
            return

    for raw_root in default_roots:
        try:
            root = Path(raw_root)
            if root.is_symlink() or not root.is_dir():
                continue
            root = root.resolve(strict=True)
        except (OSError, RuntimeError):
            continue

        add(root)
        vdf_path = root / "steamapps" / "libraryfolders.vdf"
        text = read_bounded_text(vdf_path)
        if not text:
            continue

        for match in _STEAM_PATH_FIELD.finditer(text):
            escaped = match.group(1)
            value = escaped.replace(r'\"', '"').replace(r"\\", "\\")
            candidate = _normal_absolute_path(value)
            if candidate is not None:
                add(candidate)
            if len(locations) >= MAX_STEAM_LIBRARY_LOCATIONS:
                break
        if len(locations) >= MAX_STEAM_LIBRARY_LOCATIONS:
            break

    return locations


def cached_steam_game(item: Any) -> dict[str, Any] | None:
    """Validate one persisted Steam record and rebuild its safe launch URL."""
    if not isinstance(item, dict):
        return None
    app_id = item.get("app_id")
    title = item.get("title")
    install_path = item.get("install_path")
    library_root = item.get("steam_library_root")
    if (
        not isinstance(app_id, str)
        or not _STEAM_APP_ID.fullmatch(app_id)
        or not isinstance(title, str)
        or not title.strip()
        or len(title.strip()) > MAX_STEAM_TITLE_LENGTH
        or not isinstance(install_path, str)
        or not isinstance(library_root, str)
    ):
        return None

    install = _normal_absolute_path(install_path)
    root = _normal_absolute_path(library_root)
    if install is None or root is None:
        return None
    try:
        install.relative_to(root / "steamapps" / "common")
    except ValueError:
        return None

    return {
        "id": f"steam:{app_id}",
        "title": title.strip(),
        "platform": "PC",
        "source": "Steam",
        "app_id": app_id,
        "launch": [f"steam://rungameid/{app_id}"],
        "install_path": str(install),
        "steam_library_root": str(root),
    }


def load_steam_game_cache(path: Path) -> list[dict[str, Any]] | None:
    """Read a private bounded Steam cache; None means absent/corrupt/unsafe."""
    if path.is_symlink() or path.parent.is_symlink():
        return None
    if not path.exists():
        return []
    payload = read_bounded_json(path, max_bytes=MAX_STEAM_CACHE_BYTES)
    if (
        not isinstance(payload, dict)
        or payload.get("version") != 1
        or not isinstance(payload.get("games"), list)
        or len(payload["games"]) > MAX_STEAM_CACHE_GAMES
    ):
        return None

    records: dict[str, dict[str, Any]] = {}
    for item in payload["games"]:
        game = cached_steam_game(item)
        if game is not None:
            records[game["id"]] = game
    return list(records.values())


def save_steam_game_cache(path: Path, games: Iterable[dict[str, Any]]) -> None:
    """Atomically persist minimal metadata for last-seen Steam installations."""
    records: dict[str, dict[str, Any]] = {}
    for item in games:
        game = cached_steam_game(item)
        if game is None:
            continue
        records[game["id"]] = {
            "app_id": game["app_id"],
            "title": game["title"],
            "install_path": game["install_path"],
            "steam_library_root": game["steam_library_root"],
        }
        if len(records) >= MAX_STEAM_CACHE_GAMES:
            break
    write_bounded_json(
        path,
        {"version": 1, "games": list(records.values())},
        max_bytes=MAX_STEAM_CACHE_BYTES,
    )
