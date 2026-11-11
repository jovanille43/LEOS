"""Read Lutris' local SQLite game catalog without modifying it."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote


def load_lutris_games(database_path: Path) -> list[dict[str, Any]]:
    """Return installed Lutris titles using a read-only SQLite connection."""
    if not database_path.is_file():
        return []

    uri = "file:" + quote(database_path.resolve().as_posix(), safe="/") + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=1.0)
        connection.execute("PRAGMA query_only = ON")
    except (sqlite3.Error, OSError):
        return []

    try:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(games)")
        }
        required = {"id", "name", "slug", "runner", "installed"}
        if not required.issubset(columns):
            return []

        optional = ("directory", "executable", "platform", "service")
        selected = ["id", "name", "slug", "runner", "installed"]
        selected.extend(column for column in optional if column in columns)
        quoted_columns = ", ".join(f'"{column}"' for column in selected)
        rows = connection.execute(
            f'SELECT {quoted_columns} FROM "games" WHERE "installed" = 1 ORDER BY "name" COLLATE NOCASE'
        ).fetchall()

        games: list[dict[str, Any]] = []
        for row in rows:
            record = dict(zip(selected, row))
            game_id = record.get("id")
            title = record.get("name")
            slug = record.get("slug")
            if game_id is None or not isinstance(title, str) or not title.strip():
                continue

            directory = record.get("directory")
            executable = record.get("executable")
            # Keep entries marked installed by Lutris even when an external
            # drive is temporarily disconnected. Lutris remains authoritative.
            runner = record.get("runner")
            source = "Lutris"
            if isinstance(runner, str) and runner.strip():
                source = f"Lutris · {runner.strip()}"

            games.append({
                "id": f"lutris:{game_id}",
                "title": title.strip(),
                "platform": "PC",
                "source": source,
                "app_id": str(game_id),
                "launch": [f"lutris:rungameid/{game_id}"],
                "slug": str(slug or ""),
                "install_path": str(directory or ""),
                "executable": str(executable or ""),
                "artwork": "",
            })
        return games
    except sqlite3.Error:
        return []
    finally:
        connection.close()



def find_lutris_artwork(data_home: Path, slug: str) -> Path | None:
    """Find existing local Lutris cover art without downloading or changing files."""
    if not isinstance(slug, str) or not slug or slug in {".", ".."}:
        return None
    if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in slug):
        return None

    roots = (
        data_home / "lutris" / "coverart",
        data_home / "lutris" / "icons",
    )
    extensions = (".jpg", ".jpeg", ".png", ".webp")
    for root in roots:
        for extension in extensions:
            candidate = root / f"{slug}{extension}"
            try:
                if candidate.is_file():
                    return candidate.resolve()
            except OSError:
                continue
    return None
