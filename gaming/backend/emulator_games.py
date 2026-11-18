"""Explicit-folder discovery for selected console emulator libraries.

Only user-selected folders are scanned. No global ROM search, downloads,
writes to game files, or shell commands are performed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
from pathlib import Path
from typing import Callable, Iterable


MAX_SCAN_DEPTH = 6
MAX_SCAN_ENTRIES = 20_000
MAX_SCAN_GAMES = 5_000
MAX_SOURCE_FOLDERS = 32


PLATFORM_SPECS = {
    "gamecube_wii": {
        "emulator_id": "org.DolphinEmu.dolphin-emu",
        "emulator_name": "Dolphin",
        "binaries": ("dolphin-emu", "dolphin"),
        "platform": "Nintendo",
        "extensions": frozenset({".iso", ".gcm", ".gcz", ".wbfs", ".rvz", ".wad"}),
        "arguments": lambda path: ["-e", str(path)],
    },
    "ps2": {
        "emulator_id": "net.pcsx2.PCSX2",
        "emulator_name": "PCSX2",
        "binaries": ("pcsx2-qt", "pcsx2"),
        "platform": "PlayStation",
        "extensions": frozenset({".iso", ".chd", ".cso", ".cue", ".mdf", ".nrg"}),
        "arguments": lambda path: ["-fullscreen", "--", str(path)],
    },
    "psp": {
        "emulator_id": "org.ppsspp.PPSSPP",
        "emulator_name": "PPSSPP",
        "binaries": ("PPSSPPQt", "ppsspp"),
        "platform": "PlayStation",
        "extensions": frozenset({".iso", ".cso", ".pbp"}),
        "arguments": lambda path: [str(path)],
    },
}


def _is_deployed_flatpak(app_id: str, data_home: Path, system_root: Path) -> bool:
    for app_root in (data_home / "flatpak/app" / app_id, system_root / app_id):
        try:
            if app_root.is_symlink() or not app_root.is_dir():
                continue
            for architecture in app_root.iterdir():
                if architecture.is_symlink() or not architecture.is_dir():
                    continue
                for branch in architecture.iterdir():
                    if branch.is_symlink() or not branch.is_dir():
                        continue
                    for deployment in branch.iterdir():
                        if deployment.is_dir() and (deployment / "files").is_dir():
                            return True
        except OSError:
            continue
    return False


def build_emulator_launch_prefix(
    platform_key: str,
    read_only_folder: Path,
    *,
    which: Callable[[str], str | None] | None = None,
    data_home: Path | None = None,
    system_flatpak_root: Path = Path("/var/lib/flatpak/app"),
) -> list[str]:
    """Build a native or read-only Flatpak launcher prefix for a known emulator."""
    spec = PLATFORM_SPECS.get(platform_key)
    if spec is None:
        return []
    which = shutil.which if which is None else which
    data_home = Path(data_home) if data_home is not None else Path.home() / ".local/share"
    folder = Path(read_only_folder)

    for binary in spec["binaries"]:
        executable = which(binary)
        if executable:
            return [executable]

    flatpak = which("flatpak")
    if flatpak and _is_deployed_flatpak(spec["emulator_id"], data_home, Path(system_flatpak_root)):
        return [
            flatpak,
            "run",
            f"--filesystem={folder}:ro",
            spec["emulator_id"],
        ]
    return []


def _iter_candidate_files(root: Path) -> Iterable[Path]:
    """Walk a chosen folder with strict depth/count limits and no symlink traversal."""
    pending: list[tuple[Path, int]] = [(root, 0)]
    visited_entries = 0

    while pending and visited_entries < MAX_SCAN_ENTRIES:
        directory, depth = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    visited_entries += 1
                    if visited_entries > MAX_SCAN_ENTRIES:
                        return
                    if not entry.name or entry.name.startswith(".") or entry.is_symlink():
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if depth < MAX_SCAN_DEPTH:
                                pending.append((Path(entry.path), depth + 1))
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        metadata = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if stat.S_ISREG(metadata.st_mode):
                        yield Path(entry.path)
        except OSError:
            continue


def build_emulator_launch_command(
    platform_key: str,
    content_path: Path,
    selected_root: Path,
    *,
    which: Callable[[str], str | None] | None = None,
    data_home: Path | None = None,
    system_flatpak_root: Path = Path("/var/lib/flatpak/app"),
) -> list[str]:
    """Rebuild a safe emulator launch command immediately before starting a game."""
    content_path = Path(content_path)
    selected_root = Path(selected_root)
    if content_path.is_symlink() or selected_root.is_symlink():
        return []
    try:
        root = selected_root.resolve(strict=True)
        game_file = content_path.resolve(strict=True)
        game_file.relative_to(root)
        if not root.is_dir() or not game_file.is_file():
            return []
    except (OSError, RuntimeError, ValueError):
        return []
    prefix = build_emulator_launch_prefix(
        platform_key,
        root,
        which=which,
        data_home=data_home,
        system_flatpak_root=system_flatpak_root,
    )
    if not prefix:
        return []
    spec = PLATFORM_SPECS.get(platform_key)
    if spec is None:
        return []
    return prefix + list(spec["arguments"](game_file))


def scan_emulator_folder(
    platform_key: str,
    selected_folder: Path,
    *,
    launch_prefix: list[str],
) -> list[dict[str, object]]:
    """Import supported game files from one folder explicitly chosen by the user."""
    spec = PLATFORM_SPECS.get(platform_key)
    if spec is None or not launch_prefix:
        return []

    selected_folder = Path(selected_folder).expanduser()
    if selected_folder.is_symlink() or not selected_folder.is_dir():
        return []
    try:
        root = selected_folder.resolve(strict=True)
    except (OSError, RuntimeError):
        return []
    if not root.is_dir():
        return []

    games: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for candidate in _iter_candidate_files(root):
        if candidate.suffix.casefold() not in spec["extensions"]:
            continue
        try:
            if candidate.is_symlink():
                continue
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(root)
            metadata = resolved.stat()
        except (OSError, RuntimeError, ValueError):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            continue
        path_text = str(resolved)
        if path_text in seen_paths:
            continue
        seen_paths.add(path_text)

        title = resolved.stem.strip()
        if not title or len(title) > 256:
            continue
        identity = hashlib.sha256(
            f"{platform_key}\0{path_text}".encode("utf-8")
        ).hexdigest()[:32]
        arguments = list(spec["arguments"](resolved))
        games.append({
            "id": f"emulator:{identity}",
            "title": title,
            "platform": spec["platform"],
            "source": str(spec["emulator_name"]),
            "app_id": str(spec["emulator_id"]),
            "content_path": path_text,
            "emulator_id": str(spec["emulator_id"]),
            "emulator_platform": platform_key,
            "selected_root": str(root),
            "launch": list(launch_prefix) + arguments,
            "artwork": "",
        })
        if len(games) >= MAX_SCAN_GAMES:
            break

    return sorted(games, key=lambda game: str(game["title"]).casefold())
