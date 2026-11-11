"""Pure helpers for LEOS library categories and ordering."""

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
) -> list[dict[str, Any]]:
    """Filter a sorted game list for a library category."""
    if category == "Favoris":
        return [game for game in games if game.get("id") in favorites]
    if category == "Récemment joués":
        by_id = {str(game.get("id")): game for game in games}
        return [by_id[game_id] for game_id in recent if game_id in by_id]
    if category == "Accueil":
        return list(games)
    if category == "PC Gaming":
        return [
            game for game in games
            if str(game.get("platform", "")).casefold() in {"pc", "pc gaming"}
        ]

    platform = {
        "Nintendo": "nintendo",
        "PlayStation": "playstation",
        "SEGA": "sega",
        "Arcade": "arcade",
    }.get(category)
    if platform is None:
        return list(games)
    return [
        game for game in games
        if platform in str(game.get("platform", "")).casefold()
    ]
