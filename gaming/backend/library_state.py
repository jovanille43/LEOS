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

    query = normalize_search_text(search_query)
    if not query:
        return result
    return [
        game for game in result
        if query in normalize_search_text(str(game.get("title", "")))
        or query in normalize_search_text(str(game.get("platform", "")))
        or query in normalize_search_text(str(game.get("source", "")))
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



def normalize_search_text(value: str) -> str:
    """Normalize a search string for accent-insensitive, whitespace-tolerant matching."""
    if not isinstance(value, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", normalize_display_title(value)).casefold()
    return "".join(character for character in decomposed if not unicodedata.combining(character))



def upsert_manual_game(
    games: list[dict[str, Any]], new_game: dict[str, Any]
) -> list[dict[str, Any]]:
    """Replace a manual entry with the same normalized title, retaining other games."""
    new_key = title_identity_key(str(new_game.get("title", "")))
    if not new_key:
        return list(games) + [new_game]
    retained = [
        game for game in games
        if title_identity_key(str(game.get("title", ""))) != new_key
    ]
    return retained + [new_game]
