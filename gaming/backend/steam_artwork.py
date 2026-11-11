"""Locate Steam artwork already cached on the local machine."""

from __future__ import annotations

from pathlib import Path


COVER_NAMES = (
    "library_600x900_2x.jpg",
    "library_600x900.jpg",
    "library_capsule.jpg",
)
HEADER_NAMES = (
    "library_header.jpg",
    "header.jpg",
)


def find_steam_artwork(cache_dir: Path, app_id: str) -> Path | None:
    """Find portrait artwork across Steam's current and legacy cache layouts."""
    if not app_id.isdigit():
        return None

    app_dir = cache_dir / app_id
    directories = [app_dir]
    if app_dir.is_dir():
        try:
            directories.extend(sorted(
                child for child in app_dir.iterdir() if child.is_dir()
            ))
        except OSError:
            pass

    for filename in COVER_NAMES:
        for directory in directories:
            candidate = directory / filename
            if candidate.is_file():
                return candidate

    # Older Steam clients used flat app-id-prefixed files.
    legacy_candidates = [
        cache_dir / f"{app_id}_library_600x900_2x.jpg",
        cache_dir / f"{app_id}_library_600x900.jpg",
        cache_dir / f"{app_id}_library_capsule.jpg",
    ]
    for candidate in legacy_candidates:
        if candidate.is_file():
            return candidate

    for filename in HEADER_NAMES:
        for directory in directories:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
    legacy_header = cache_dir / f"{app_id}_header.jpg"
    return legacy_header if legacy_header.is_file() else None
