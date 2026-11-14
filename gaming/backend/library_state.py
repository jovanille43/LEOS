"""Pure helpers for LEOS library categories, search and ordering."""

from __future__ import annotations

from typing import Any
import json
import os
import tempfile
import shlex
from pathlib import Path
import re
import unicodedata

from leos_core.text import normalize_search_text
from leos_core.json_utils import json_nesting_within_limit


MAX_LIBRARY_STATE_FILE_BYTES = 2 * 1024 * 1024
MAX_MANUAL_GAMES = 5000
MAX_MANUAL_TITLE_LENGTH = 256
MAX_MANUAL_PLATFORM_LENGTH = 64
MAX_MANUAL_COMMAND_LENGTH = 8192
MAX_MANUAL_ARGUMENTS = 32
MAX_MANUAL_ARGUMENT_LENGTH = 2048


MAX_LIBRARY_TEXT_FILE_BYTES = 1024 * 1024


def write_bounded_json(
    path: Path,
    value: Any,
    max_bytes: int = MAX_LIBRARY_STATE_FILE_BYTES,
) -> None:
    """Atomically write private JSON state with symlink and size protections."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("Invalid JSON state size limit")
    payload = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(payload) > max_bytes:
        raise ValueError("JSON state exceeds its storage limit")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or path.is_symlink():
        raise OSError("JSON state path cannot be a symbolic link")
    os.chmod(path.parent, 0o700)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=".tmp", dir=path.parent
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(
                path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def read_bounded_text(path: Path, max_bytes: int = MAX_LIBRARY_TEXT_FILE_BYTES) -> str | None:
    """Read a local text metadata file with a strict byte limit."""
    if type(max_bytes) is not int or max_bytes < 0:
        return None
    if path.is_symlink() or path.parent.is_symlink():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def read_bounded_json(path: Path, max_bytes: int = MAX_LIBRARY_STATE_FILE_BYTES) -> Any | None:
    """Read local library state without allowing oversized or linked files into memory."""
    if type(max_bytes) is not int or max_bytes < 0:
        return None
    if path.is_symlink() or path.parent.is_symlink():
        return None
    try:
        with path.open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None
        text = raw.decode("utf-8")
        if not json_nesting_within_limit(text):
            return None
        return json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
        return None


CATEGORIES = (
    "Accueil",
    "PC Gaming",
    "Nintendo",
    "PlayStation",
    "SEGA",
    "Arcade",
    "Émulation",
    "Favoris",
    "Récemment joués",
)


def filter_games(
    games: list[dict[str, Any]],
    category: str,
    favorites: set[str],
    recent: list[str],
    search_query: str = "",
) -> list[dict[str, Any]]:
    """Filter games by category and a case-insensitive search query."""
    if category == "Favoris":
        result = [game for game in games if game.get("id") in favorites]
    elif category == "Récemment joués":
        by_id = {str(game.get("id")): game for game in games}
        result = [by_id[game_id] for game_id in recent if game_id in by_id]
    elif category == "Accueil":
        result = list(games)
    elif category == "Émulation":
        result = [
            game for game in games
            if "retroarch" in str(game.get("source", "")).casefold()
            or "émulation" in str(game.get("platform", "")).casefold()
            or "emulation" in str(game.get("platform", "")).casefold()
        ]
    elif category == "PC Gaming":
        result = [
            game for game in games
            if str(game.get("platform", "")).casefold() in {"pc", "pc gaming"}
        ]
    else:
        platform = {
            "Nintendo": "nintendo",
            "PlayStation": "playstation",
            "SEGA": "sega",
            "Arcade": "arcade",
        }.get(category)
        result = (
            list(games)
            if platform is None
            else [
                game for game in games
                if platform in str(game.get("platform", "")).casefold()
            ]
        )

    query = normalize_search_text(search_query)
    if not query:
        return result
    return [
        game for game in result
        if query in normalize_search_text(str(game.get("title", "")))
        or query in normalize_search_text(str(game.get("platform", "")))
        or query in normalize_search_text(str(game.get("source", "")))
        or query in normalize_search_text(str(game.get("app_id", "")))
        or query in normalize_search_text(str(game.get("id", "")))
    ]



def normalize_display_title(title: str) -> str:
    """Trim and collapse whitespace without changing visible naming."""
    if not isinstance(title, str):
        return ""
    return re.sub(r"\s+", " ", title).strip()


def validate_manual_game_input(
    title: object, platform: object, command: object
) -> tuple[str, str, list[str]] | None:
    """Validate manual game fields before they reach persistent storage or QProcess."""
    if not all(isinstance(value, str) for value in (title, platform, command)):
        return None
    clean_title = normalize_display_title(title)
    clean_platform = normalize_display_title(platform) or "PC"
    clean_command = command.strip()
    if (
        not clean_title or len(clean_title) > MAX_MANUAL_TITLE_LENGTH
        or len(clean_platform) > MAX_MANUAL_PLATFORM_LENGTH
        or not clean_command or len(clean_command) > MAX_MANUAL_COMMAND_LENGTH
        or "\x00" in clean_command
    ):
        return None
    try:
        launch = shlex.split(clean_command, posix=True)
    except ValueError:
        return None
    if (
        not launch or len(launch) > MAX_MANUAL_ARGUMENTS
        or any(not part or len(part) > MAX_MANUAL_ARGUMENT_LENGTH or "\x00" in part for part in launch)
    ):
        return None
    return clean_title, clean_platform, launch


def title_identity_key(title: str) -> str:
    """Conservative identity key; punctuation and edition markers are retained."""
    return unicodedata.normalize("NFC", normalize_display_title(title)).casefold()


def duplicate_title_metadata(games: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Expose exact-title matches without merging or deleting provider records."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for game in games:
        key = title_identity_key(str(game.get("title", "")))
        if key:
            grouped.setdefault(key, []).append(game)
    metadata: dict[str, dict[str, Any]] = {}
    for matches in grouped.values():
        if len(matches) < 2:
            continue
        sources = list(dict.fromkeys(
            normalize_display_title(str(game.get("source", "")))
            for game in matches if game.get("source")
        ))
        for game in matches:
            metadata[str(game.get("id", ""))] = {
                "count": len(matches),
                "sources": sources,
            }
    return metadata



def upsert_manual_game(
    games: list[dict[str, Any]], new_game: dict[str, Any]
) -> list[dict[str, Any]]:
    """Replace a manual entry with the same normalized title, retaining other games."""
    new_key = title_identity_key(str(new_game.get("title", "")))
    if not new_key:
        return list(games) + [new_game]
    def is_same_manual_entry(game: dict[str, Any]) -> bool:
        game_id = game.get("id")
        return (
            isinstance(game_id, str)
            and game_id.startswith("manual:")
            and title_identity_key(str(game.get("title", ""))) == new_key
        )

    matching = [game for game in games if is_same_manual_entry(game)]
    retained = [game for game in games if not is_same_manual_entry(game)]
    replacement = dict(new_game)
    if matching:
        previous_id = matching[0].get("id")
        if isinstance(previous_id, str) and previous_id:
            replacement["id"] = previous_id
    return retained + [replacement]
