"""Pure helpers for LEOS library categories, search and ordering."""

from __future__ import annotations

from typing import Any
import json
from pathlib import Path
import re
import unicodedata

from leos_core.text import normalize_search_text


MAX_LIBRARY_STATE_FILE_BYTES = 2 * 1024 * 1024


def read_bounded_json(path: Path, max_bytes: int = MAX_LIBRARY_STATE_FILE_BYTES) -> Any | None:
    """Read local library state without allowing oversized files into memory."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None
        return json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return None


CATEGORIES = (
    "Accueil",
    "PC Gaming",
    "Nintendo",
    "PlayStation",
    "SEGA",
    "Arcade",
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
