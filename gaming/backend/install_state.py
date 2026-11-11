"""Truthful installation-state checks for imported game records."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def installation_status(game: dict[str, Any]) -> str:
    """Describe local file availability without exposing private paths."""
    candidates: list[Path] = []
    for key in ("install_path", "executable"):
        value = game.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            continue
        candidates.append(candidate)

    if not candidates:
        return "État inconnu"
    for candidate in candidates:
        try:
            if candidate.exists():
                return "Installé"
        except OSError:
            continue
    return "Fichiers absents"
