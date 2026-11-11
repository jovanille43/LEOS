"""Read installed Heroic/Legendary game manifests without changing them."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from typing import Any


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def find_heroic_artwork(record: dict[str, Any]) -> str:
    """Return a verified local artwork file from a Heroic manifest record."""
    keys = ("art_cover", "artCover", "art_square", "artSquare", "cover", "icon")
    for key in keys:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = Path(value.strip()).expanduser()
        if not candidate.is_absolute() or candidate.suffix.lower() not in _IMAGE_SUFFIXES:
            continue
        try:
            if candidate.is_file():
                return candidate.resolve().as_uri()
        except OSError:
            continue
    return ""


def load_heroic_games(installed_file: Path, runner: str) -> list[dict[str, Any]]:
    """Parse a local Heroic installed.json file into LEOS game records."""
    if runner not in {"legendary", "gog", "nile"}:
        return []
    try:
        payload = json.loads(installed_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(payload, dict):
        records = payload.items()
    elif isinstance(payload, list):
        records = ((str(index), value) for index, value in enumerate(payload))
    else:
        return []

    games: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key, record in records:
        if not isinstance(record, dict):
            continue
        if record.get("is_dlc") or record.get("isDLC"):
            continue

        app_name = record.get("app_name") or record.get("appName") or key
        if not isinstance(app_name, str) or not app_name.strip():
            continue
        app_name = app_name.strip()
        normalized_id = app_name.casefold()
        if normalized_id in seen:
            continue

        install_path = (
            record.get("install_path")
            or record.get("installPath")
            or record.get("install_dir")
        )
        if not isinstance(install_path, str):
            install_path = ""
        install_dir = Path(install_path).expanduser() if install_path.strip() else None

        title = (
            record.get("title")
            or record.get("app_title")
            or record.get("appTitle")
            or record.get("name")
            or app_name
        )
        if not isinstance(title, str) or not title.strip():
            title = app_name

        runner_label = {
            "legendary": "Epic Games · Heroic",
            "gog": "GOG · Heroic",
            "nile": "Amazon Games · Heroic",
        }[runner]
        launch_url = (
            "heroic://launch?appName="
            + quote(app_name, safe="")
            + "&runner="
            + runner
            + "&gui=false"
        )
        games.append({
            "id": f"heroic:{runner}:{normalized_id}",
            "title": title.strip(),
            "platform": "PC",
            "source": runner_label,
            "app_id": app_name,
            "launch": [launch_url],
            "install_path": str(install_dir) if install_dir else "",
            "artwork": find_heroic_artwork(record),
        })
        seen.add(normalized_id)
    return games
