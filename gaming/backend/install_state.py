"""Truthful installation-state checks for imported game records."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def installation_status(game: dict[str, Any]) -> str:
    """Describe local file availability without exposing private paths."""
    candidates: list[tuple[Path, str]] = []
    for key, expected_type in (
        ("install_path", "directory"),
        ("executable", "file"),
    ):
        value = game.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            candidates.append((candidate, expected_type))

    if not candidates:
        return "État inconnu"
    for candidate, expected_type in candidates:
        try:
            if expected_type == "directory" and candidate.is_dir():
                return "Installé"
            if expected_type == "file" and candidate.is_file():
                return "Installé"
        except OSError:
            continue
    return "Fichiers absents"
