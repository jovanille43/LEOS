"""Safe, bounded directory navigation for the LEOS emulator folder picker."""

from __future__ import annotations

import os
from pathlib import Path


MAX_BROWSE_DIRECTORY_ENTRIES = 256


def resolve_browsable_directory(path: Path) -> Path | None:
    """Resolve an existing local directory without accepting a symlink."""
    candidate = Path(path).expanduser()
    try:
        if candidate.is_symlink() or not candidate.is_dir():
            return None
        resolved = candidate.resolve(strict=True)
        return resolved if resolved.is_dir() else None
    except (OSError, RuntimeError):
        return None


def list_child_directories(path: Path) -> list[str]:
    """List a bounded, sorted set of visible immediate child directories only."""
    root = resolve_browsable_directory(path)
    if root is None:
        return []

    names: list[str] = []
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                if len(names) >= MAX_BROWSE_DIRECTORY_ENTRIES:
                    break
                if not entry.name or entry.name.startswith(".") or entry.is_symlink():
                    continue
                try:
                    if entry.is_dir(follow_symlinks=False):
                        names.append(entry.name)
                except OSError:
                    continue
    except OSError:
        return []
    return sorted(names, key=str.casefold)


def resolve_child_directory(current_path: Path, name: str) -> Path | None:
    """Resolve one visible child name, rejecting traversal and symlink escapes."""
    if (
        not isinstance(name, str)
        or not name
        or name in {".", ".."}
        or "\x00" in name
        or "/" in name
        or "\\" in name
        or name.startswith(".")
    ):
        return None
    root = resolve_browsable_directory(current_path)
    if root is None:
        return None
    candidate = root / name
    if candidate.is_symlink():
        return None
    resolved = resolve_browsable_directory(candidate)
    if resolved is None:
        return None
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    return resolved if len(relative.parts) == 1 else None


def parent_directory(current_path: Path) -> Path | None:
    """Return the real parent directory, or None when already at filesystem root."""
    current = resolve_browsable_directory(current_path)
    if current is None or current.parent == current:
        return None
    return resolve_browsable_directory(current.parent)
