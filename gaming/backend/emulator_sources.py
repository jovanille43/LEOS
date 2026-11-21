"""Pure, bounded persistence helpers for Gaming emulator source folders."""

from __future__ import annotations

from pathlib import Path

from .emulator_games import MAX_SOURCE_FOLDERS, PLATFORM_SPECS
from .library_state import read_bounded_json, write_bounded_json


def remove_emulator_source_folder(
    state_file: Path,
    platform_key: str,
    folder: str,
) -> bool:
    """Forget one user-selected source; never touch the external game files."""
    state_file = Path(state_file)
    if (
        not isinstance(platform_key, str)
        or platform_key not in PLATFORM_SPECS
        or not isinstance(folder, str)
        or not folder
        or len(folder) > 4096
        or "\x00" in folder
        or not Path(folder).is_absolute()
    ):
        return False
    if (
        state_file.is_symlink()
        or state_file.parent.is_symlink()
        or not state_file.is_file()
    ):
        return False

    raw = read_bounded_json(state_file)
    if not isinstance(raw, list) or len(raw) > MAX_SOURCE_FOLDERS:
        return False

    remaining: list[dict[str, str]] = []
    removed = False
    for item in raw:
        if (
            not isinstance(item, dict)
            or set(item) != {"platform", "path"}
            or item.get("platform") not in PLATFORM_SPECS
            or not isinstance(item.get("path"), str)
            or not item["path"]
            or len(item["path"]) > 4096
            or "\x00" in item["path"]
            or not Path(item["path"]).is_absolute()
        ):
            return False
        if item["platform"] == platform_key and item["path"] == folder:
            removed = True
            continue
        remaining.append({
            "platform": item["platform"],
            "path": item["path"],
        })

    if not removed:
        return False
    try:
        write_bounded_json(state_file, remaining)
    except (OSError, ValueError):
        return False
    return True
