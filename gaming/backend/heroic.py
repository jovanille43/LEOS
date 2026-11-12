"""Read installed Heroic/Legendary game manifests without changing them."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from typing import Any

from leos_core.json_utils import json_nesting_within_limit


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MAX_HEROIC_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_HEROIC_GAMES = 20_000


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
        # Installed manifests are local data, but bound reads so a corrupt or
        # unexpectedly large file cannot stall library discovery indefinitely.
        with installed_file.open("rb") as stream:
            raw = stream.read(MAX_HEROIC_MANIFEST_BYTES + 1)
        if len(raw) > MAX_HEROIC_MANIFEST_BYTES:
            return []
        text = raw.decode("utf-8-sig")
        if not json_nesting_within_limit(text):
            return []
        payload = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError):
        return []

    if isinstance(payload, dict):
        records = payload.items()
    elif isinstance(payload, list):
        records = ((str(index), value) for index, value in enumerate(payload))
    else:
        return []

    games: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, (key, record) in enumerate(records):
        if index >= MAX_HEROIC_GAMES:
            break
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
