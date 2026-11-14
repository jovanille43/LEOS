"""Safe automatic filing of completed game downloads into LEOS ROM folders.

Only a conservative set of unambiguous, single-file formats is moved. The
organizer never extracts archives, inspects ROM contents, executes files, or
overwrites an existing destination.
"""

from __future__ import annotations

import os
from itertools import islice
import re
import shlex
import stat
import time
from pathlib import Path

MAX_DOWNLOAD_SCAN_ENTRIES = 250
MAX_DOWNLOAD_CONFIG_BYTES = 16 * 1024
DEFAULT_STABILITY_SECONDS = 15.0
REQUIRED_STABLE_RECHECKS = 2

# Extensions whose system is sufficiently unambiguous to file without asking.
# Ambiguous formats (.iso, .bin, .cue, .chd, .m3u, .zip, .7z, .pkg, .rvz)
# are deliberately excluded: moving them blindly could misclassify a game.
DESTINATION_BY_EXTENSION: dict[str, tuple[str, str]] = {
    ".nes": ("Nintendo", "NES"),
    ".fds": ("Nintendo", "Famicom Disk System"),
    ".gb": ("Nintendo", "Game Boy"),
    ".gbc": ("Nintendo", "Game Boy Color"),
    ".gba": ("Nintendo", "Game Boy Advance"),
    ".nds": ("Nintendo", "Nintendo DS"),
    ".3ds": ("Nintendo", "Nintendo 3DS"),
    ".n64": ("Nintendo", "Nintendo 64"),
    ".z64": ("Nintendo", "Nintendo 64"),
    ".v64": ("Nintendo", "Nintendo 64"),
    ".sfc": ("Nintendo", "Super Nintendo"),
    ".smc": ("Nintendo", "Super Nintendo"),
    ".gcm": ("Nintendo", "GameCube"),
    ".wbfs": ("Nintendo", "Wii"),
    ".wua": ("Nintendo", "Wii U"),
    ".wuhb": ("Nintendo", "Wii U"),
    ".wud": ("Nintendo", "Wii U"),
    ".wux": ("Nintendo", "Wii U"),
    ".sms": ("SEGA", "Master System"),
    ".gg": ("SEGA", "Game Gear"),
    ".md": ("SEGA", "Mega Drive"),
    ".gen": ("SEGA", "Mega Drive"),
    ".32x": ("SEGA", "32X"),
    ".pbp": ("PlayStation", "PSP"),
    ".cso": ("PlayStation", "PSP"),
    ".zso": ("PlayStation", "PSP"),
}

PARTIAL_SUFFIXES = (".part", ".crdownload", ".download", ".tmp")


def resolve_download_directory(
    home: Path | None = None,
    config_home: Path | None = None,
) -> Path:
    """Resolve XDG_DOWNLOAD_DIR without evaluating shell expressions."""
    base = Path(home or Path.home()).expanduser().resolve()
    config = Path(config_home) if config_home is not None else base / ".config"
    user_dirs = config / "user-dirs.dirs"
    try:
        if user_dirs.is_symlink():
            raise OSError("User directories configuration is a symbolic link")
        raw = user_dirs.read_bytes()
        if len(raw) <= MAX_DOWNLOAD_CONFIG_BYTES:
            text = raw.decode("utf-8")
            for line in text.splitlines():
                match = re.match(r'^\s*XDG_DOWNLOAD_DIR\s*=\s*(.+?)\s*$', line)
                if not match:
                    continue
                try:
                    parts = shlex.split(match.group(1), comments=True, posix=True)
                except ValueError:
                    break
                if len(parts) != 1:
                    break
                value = parts[0]
                if value.startswith("${HOME}/"):
                    value = str(base / value[len("${HOME}/"):])
                elif value.startswith("$HOME/"):
                    value = str(base / value[len("$HOME/"):])
                else:
                    # Only literal absolute paths inside HOME are accepted.
                    if "$" in value or value.startswith("~"):
                        break
                candidate = Path(value)
                if not candidate.is_absolute():
                    break
                resolved = candidate.resolve(strict=False)
                resolved.relative_to(base)
                if resolved != base and not resolved.is_symlink():
                    return resolved
                break
    except (OSError, UnicodeError, ValueError):
        pass

    for name in ("Downloads", "Téléchargements"):
        candidate = base / name
        if candidate.is_dir() and not candidate.is_symlink():
            return candidate
    return base / "Downloads"


def _collision_free_path(directory: Path, filename: str) -> Path:
    target = directory / filename
    if not target.exists():
        return target
    source = Path(filename)
    for index in range(2, 10_002):
        candidate = directory / f"{source.stem} ({index}){source.suffix}"
        if not candidate.exists():
            return candidate
    raise OSError("Too many files with the same name in the target folder")


class DownloadOrganizer:
    """Poll a downloads folder and move only completed, known game files."""

    def __init__(
        self,
        downloads_dir: Path | None = None,
        emulation_root: Path | None = None,
        *,
        home: Path | None = None,
        stability_seconds: float = DEFAULT_STABILITY_SECONDS,
        max_entries: int = MAX_DOWNLOAD_SCAN_ENTRIES,
    ) -> None:
        self.home = Path(home or Path.home()).expanduser().resolve()
        self.downloads_dir = Path(downloads_dir) if downloads_dir is not None else resolve_download_directory(self.home)
        self.emulation_root = Path(emulation_root) if emulation_root is not None else self.home / "Emulation" / "ROMs"
        self.stability_seconds = max(0.0, float(stability_seconds))
        self.max_entries = max(1, min(int(max_entries), MAX_DOWNLOAD_SCAN_ENTRIES))
        self._observed: dict[str, tuple[int, int, int]] = {}

    def poll(self, *, now: float | None = None) -> list[dict[str, str]]:
        """Move stable, recognized files; return a record for each successful move."""
        current_time = time.time() if now is None else float(now)
        downloads = self.downloads_dir
        root = self.emulation_root
        try:
            if downloads.is_symlink() or root.is_symlink():
                return []
            downloads_resolved = downloads.resolve(strict=True)
            root_resolved = root.resolve(strict=False)
            if downloads_resolved == root_resolved:
                return []
            downloads_resolved.relative_to(self.home)
            root_resolved.relative_to(self.home)
        except (OSError, ValueError):
            return []

        # The two trees must be disjoint; otherwise the organizer could loop
        # over its own destination or move files into the watched Downloads tree.
        try:
            root_resolved.relative_to(downloads_resolved)
            return []
        except ValueError:
            pass
        try:
            downloads_resolved.relative_to(root_resolved)
            return []
        except ValueError:
            pass

        try:
            with os.scandir(downloads_resolved) as entries:
                candidates = list(islice(entries, self.max_entries))
        except OSError:
            return []

        active: set[str] = set()
        moved: list[dict[str, str]] = []
        for entry in candidates:
            try:
                if entry.name.startswith(".") or entry.is_symlink():
                    continue
                path = Path(entry.path)
                if path.suffix.casefold() in PARTIAL_SUFFIXES:
                    continue
                destination = DESTINATION_BY_EXTENSION.get(path.suffix.casefold())
                if destination is None or not entry.is_file(follow_symlinks=False):
                    continue
                info = entry.stat(follow_symlinks=False)
                if not stat.S_ISREG(info.st_mode) or info.st_size <= 0:
                    continue
                if len(str(path)) > 4096 or len(entry.name) > 240:
                    continue

                key = str(path)
                active.add(key)
                signature = (info.st_size, info.st_mtime_ns)
                previous = self._observed.get(key)
                if previous is None or previous[:2] != signature:
                    self._observed[key] = (signature[0], signature[1], 0)
                    continue

                stable_rechecks = previous[2] + 1
                self._observed[key] = (signature[0], signature[1], stable_rechecks)
                if (
                    stable_rechecks < REQUIRED_STABLE_RECHECKS
                    or current_time - info.st_mtime < self.stability_seconds
                ):
                    continue

                system, console = destination
                target_directory = root_resolved / system / console
                target_directory.mkdir(parents=True, exist_ok=True)
                real_target_directory = target_directory.resolve(strict=True)
                real_target_directory.relative_to(root_resolved)
                if target_directory.is_symlink():
                    continue
                target = _collision_free_path(real_target_directory, entry.name)
                # rename is atomic on the usual single-filesystem home layout.
                # It is never used with an existing destination.
                if target.exists():
                    continue
                path.rename(target)
                self._observed.pop(key, None)
                moved.append({
                    "name": target.name,
                    "system": system,
                    "console": console,
                    "destination": str(target),
                })
            except (OSError, RuntimeError, ValueError):
                continue

        self._observed = {
            key: value for key, value in self._observed.items()
            if key in active
        }
        return moved
