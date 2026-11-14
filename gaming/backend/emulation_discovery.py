"""Safe, bounded discovery of locally stored emulation game files.

The scanner only reads directory entries and file metadata. It never opens ROM
contents, executes files, follows symbolic links, or downloads anything.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

MAX_SCAN_DEPTH = 8
MAX_SCAN_FILES = 10_000
MAX_PATH_LENGTH = 4096

# Broad formats shared by common emulators. Extensions are intentionally
# conservative; archives are not unpacked and disc images are not inspected.
PLATFORM_EXTENSIONS: tuple[tuple[str, frozenset[str]], ...] = (
    ("Nintendo", frozenset({".nes", ".fds", ".gb", ".gbc", ".gba", ".nds", ".3ds", ".n64", ".z64", ".v64", ".iso", ".gcm", ".wbfs", ".rvz", ".wud", ".wux"})),
    ("PlayStation", frozenset({".cue", ".bin", ".iso", ".chd", ".pbp", ".cso", ".zso", ".pkg", ".m3u"})),
    ("SEGA", frozenset({".sms", ".gg", ".md", ".gen", ".32x", ".cue", ".iso"})),
    ("Arcade", frozenset({".zip", ".7z"})),
    ("Émulation", frozenset({".nes", ".fds", ".gb", ".gbc", ".gba", ".nds", ".3ds", ".n64", ".z64", ".v64", ".iso", ".gcm", ".wbfs", ".rvz", ".wud", ".wux", ".cue", ".bin", ".chd", ".pbp", ".cso", ".zso", ".pkg", ".m3u", ".sms", ".gg", ".md", ".gen", ".32x", ".zip", ".7z"})),
)

EXTENSION_PLATFORM: dict[str, str] = {}
for _platform, _extensions in PLATFORM_EXTENSIONS:
    for _extension in _extensions:
        # Prefer a console-specific category over the generic catch-all.
        if _platform != "Émulation":
            EXTENSION_PLATFORM.setdefault(_extension, _platform)
# Shared disc/container extensions do not identify a console on their own.
for _ambiguous in (".iso", ".cue", ".bin", ".zip", ".7z", ".m3u"):
    EXTENSION_PLATFORM[_ambiguous] = "Émulation"


def default_scan_roots(home: Path | None = None) -> tuple[Path, ...]:
    """Return conventional user game folders; no system-wide locations."""
    base = home if home is not None else Path.home()
    return tuple(base / name for name in ("Games", "ROMs", "Roms", "Emulation"))


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _platform_for(path: Path) -> str:
    return EXTENSION_PLATFORM.get(path.suffix.casefold(), "Émulation")


def discover_emulated_games(
    roots: Iterable[Path] | None = None,
    *,
    max_files: int = MAX_SCAN_FILES,
    max_depth: int = MAX_SCAN_DEPTH,
) -> list[dict[str, str]]:
    """Discover candidate game files below explicit or conventional user roots.

    Results are metadata-only entries. The caller may merge them into the
    library; it remains responsible for asking before launching a game.
    """
    if type(max_files) is not int or not 1 <= max_files <= MAX_SCAN_FILES:
        return []
    if type(max_depth) is not int or not 0 <= max_depth <= MAX_SCAN_DEPTH:
        return []

    candidates = default_scan_roots() if roots is None else tuple(roots)
    safe_roots: list[Path] = []
    for candidate in candidates:
        try:
            root = Path(candidate).expanduser()
            if root.is_symlink() or not root.is_dir():
                continue
            resolved = root.resolve(strict=True)
            if resolved not in safe_roots:
                safe_roots.append(resolved)
        except (OSError, RuntimeError, TypeError, ValueError):
            continue

    found: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    visited_files = 0

    for root in safe_roots:
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack and visited_files < max_files:
            directory, depth = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if visited_files >= max_files:
                            break
                        try:
                            if entry.is_symlink() or entry.name.startswith("."):
                                continue
                            path = Path(entry.path)
                            if len(str(path)) > MAX_PATH_LENGTH:
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                if depth < max_depth:
                                    stack.append((path, depth + 1))
                                continue
                            if not entry.is_file(follow_symlinks=False):
                                continue
                            visited_files += 1
                            extension = path.suffix.casefold()
                            if extension not in EXTENSION_PLATFORM:
                                continue
                            resolved = path.resolve(strict=True)
                            if not _is_within(resolved, root):
                                continue
                            identity = str(resolved)
                            if identity in seen_paths:
                                continue
                            seen_paths.add(identity)
                            title = path.stem.strip()
                            if not title:
                                continue
                            digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
                            found.append({
                                "id": f"emulator:{digest}",
                                "title": title,
                                "platform": _platform_for(path),
                                "source": "Fichiers locaux",
                                "path": identity,
                                "app_id": "",
                            })
                        except (OSError, RuntimeError, ValueError):
                            continue
            except (OSError, PermissionError):
                continue

    return sorted(found, key=lambda game: (game["title"].casefold(), game["path"].casefold()))
