"""Pure helpers for LEOS library categories, search and ordering."""

from __future__ import annotations

from typing import Any


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
