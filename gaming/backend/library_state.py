"""Pure helpers for LEOS library categories, search and ordering."""

from __future__ import annotations

from typing import Any
import re
import unicodedata


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

    query = search_query.strip().casefold()
    if not query:
        return result
    return [
        game for game in result
        if query in str(game.get("title", "")).casefold()
        or query in str(game.get("platform", "")).casefold()
        or query in str(game.get("source", "")).casefold()
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
