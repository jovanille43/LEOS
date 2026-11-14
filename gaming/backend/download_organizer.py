"""Safe automatic filing of completed game downloads into LEOS ROM folders.

Only a conservative set of unambiguous, single-file formats is moved. A ZIP
is extracted only when it contains exactly one recognized game file. The
organizer never executes files or overwrites an existing destination.
"""

from __future__ import annotations

import errno
import os
from itertools import islice
import re
import shlex
import shutil
import stat
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath

MAX_DOWNLOAD_SCAN_ENTRIES = 250
MAX_DOWNLOAD_DIRECTORY_ENTRIES = 5_000
MAX_ARCHIVE_ENTRIES = 2_000
MAX_ARCHIVE_FILE_BYTES = 32 * 1024 ** 3
MAX_ARCHIVE_MEMBER_BYTES = 16 * 1024 ** 3
MAX_ARCHIVE_COMPRESSION_RATIO = 500
MAX_DOWNLOAD_CONFIG_BYTES = 16 * 1024
DEFAULT_STABILITY_SECONDS = 15.0
REQUIRED_STABLE_RECHECKS = 2

# Extensions whose system is sufficiently unambiguous to file without asking.
# Ambiguous formats (.iso, .bin, .cue, .chd, .m3u, .7z, .rar, .pkg, .rvz)
# are deliberately excluded: moving them blindly could misclassify a game.
# ZIP archives are handled separately and only when exactly one safe game file
# can be identified inside.
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
    if config_home is not None:
        config = Path(config_home)
    else:
        configured = os.environ.get("XDG_CONFIG_HOME", "")
        candidate_config = Path(configured).expanduser() if configured else base / ".config"
        config = candidate_config if candidate_config.is_absolute() else base / ".config"
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
                home_relative = value.startswith("${HOME}/") or value.startswith("$HOME/")
                if value.startswith("${HOME}/"):
                    value = str(base / value[len("${HOME}/"):])
                elif value.startswith("$HOME/"):
                    value = str(base / value[len("$HOME/"):])
                elif "$" in value or value.startswith("~"):
                    break
                candidate = Path(value)
                if not candidate.is_absolute():
                    break
                resolved = candidate.resolve(strict=False)
                if home_relative:
                    resolved.relative_to(base)
                if resolved != base and resolved != Path(resolved.anchor):
                    return resolved
                break
    except (OSError, UnicodeError, ValueError):
        pass

    for name in ("Downloads", "Téléchargements"):
        candidate = base / name
        if candidate.is_dir() and not candidate.is_symlink():
            return candidate
    return base / "Downloads"


def _move_without_overwrite(
    source: Path,
    destination: Path,
    expected_signature: tuple[int, int] | None = None,
) -> None:
    """Move without replacing any existing destination, including across filesystems."""
    before = source.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise OSError("Download is not a regular file")
    if expected_signature is not None and (
        before.st_size, before.st_mtime_ns
    ) != expected_signature:
        raise OSError("Download changed before being moved")
    try:
        # A hard link is an atomic no-replace operation on a single filesystem.
        os.link(source, destination, follow_symlinks=False)
        current = source.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(current.st_mode)
            or (current.st_size, current.st_mtime_ns) != (before.st_size, before.st_mtime_ns)
        ):
            destination.unlink()
            raise OSError("Download changed while being moved")
        try:
            source.unlink()
        except OSError:
            try:
                destination.unlink()
            except OSError:
                pass
            raise
        return
    except FileExistsError:
        raise
    except OSError as error:
        if error.errno not in {
            errno.EXDEV,
            errno.EPERM,
            errno.EACCES,
            errno.EMLINK,
            getattr(errno, "EOPNOTSUPP", errno.EPERM),
            getattr(errno, "ENOTSUP", errno.EPERM),
        }:
            raise

    if shutil.disk_usage(destination.parent).free < before.st_size + 16 * 1024 * 1024:
        raise OSError("Not enough free space to safely move the download")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".leos-move-", dir=destination.parent
    )
    temporary = Path(temporary_name)
    copied = 0
    try:
        with source.open("rb") as incoming, os.fdopen(descriptor, "wb") as outgoing:
            while True:
                chunk = incoming.read(1024 * 1024)
                if not chunk:
                    break
                copied += len(chunk)
                if copied > before.st_size:
                    raise OSError("Download changed while being copied")
                outgoing.write(chunk)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        after = source.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(after.st_mode)
            or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
            or copied != before.st_size
        ):
            raise OSError("Download changed while being copied")
        try:
            os.link(temporary, destination, follow_symlinks=False)
        except FileExistsError:
            raise
        temporary.unlink()
        try:
            source.unlink()
        except OSError:
            try:
                destination.unlink()
            except OSError:
                pass
            raise
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


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


def _extract_single_game_zip(
    archive_path: Path,
    root: Path,
    expected_signature: tuple[int, int],
) -> dict[str, str] | None:
    """Extract one unambiguous ROM from a stable ZIP without trusting its paths."""
    temporary_path: Path | None = None
    archived_original: Path | None = None
    original_path = archive_path
    try:
        archive_info = archive_path.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(archive_info.st_mode)
            or archive_info.st_size > MAX_ARCHIVE_FILE_BYTES
            or (archive_info.st_size, archive_info.st_mtime_ns) != expected_signature
        ):
            return None
        with zipfile.ZipFile(archive_path, "r") as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_ARCHIVE_ENTRIES:
                return None

            candidates: list[tuple[zipfile.ZipInfo, tuple[str, str]]] = []
            for member in members:
                if member.is_dir() or member.flag_bits & 0x1:
                    continue
                member_path = PurePosixPath(member.filename)
                if (
                    member_path.is_absolute()
                    or not member_path.parts
                    or any(part in {"", ".", ".."} for part in member_path.parts)
                    or "\\" in member.filename
                    or ":" in member_path.parts[0]
                ):
                    continue
                if any(ord(character) < 32 for character in member_path.name):
                    continue
                if len(member_path.name) > 240:
                    continue
                mode = (member.external_attr >> 16) & 0xFFFF
                file_type = stat.S_IFMT(mode)
                if file_type not in (0, stat.S_IFREG):
                    continue
                destination = DESTINATION_BY_EXTENSION.get(
                    Path(member_path.name).suffix.casefold()
                )
                if destination is not None:
                    candidates.append((member, destination))

            # Multi-game packs need a user choice; never guess which one to keep.
            if len(candidates) != 1:
                return None
            member, (system, console) = candidates[0]
            if (
                member.file_size <= 0
                or member.file_size > MAX_ARCHIVE_MEMBER_BYTES
                or member.compress_size <= 0
                or member.file_size / member.compress_size > MAX_ARCHIVE_COMPRESSION_RATIO
            ):
                return None

            target_directory = root / system / console
            target_directory.mkdir(parents=True, exist_ok=True)
            real_target_directory = target_directory.resolve(strict=True)
            real_target_directory.relative_to(root)
            if target_directory.is_symlink():
                return None
            final_target = _collision_free_path(
                real_target_directory, PurePosixPath(member.filename).name
            )
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=".leos-extract-", suffix=final_target.suffix,
                dir=real_target_directory,
            )
            temporary_path = Path(temporary_name)
            copied = 0
            with os.fdopen(descriptor, "wb") as output, archive.open(member, "r") as source:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > member.file_size or copied > MAX_ARCHIVE_MEMBER_BYTES:
                        raise ValueError("Archive member exceeded its declared size")
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            if copied != member.file_size:
                raise ValueError("Incomplete archive member")

        current = archive_path.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(current.st_mode)
            or (current.st_size, current.st_mtime_ns) != expected_signature
        ):
            raise ValueError("Archive changed while being processed")

        archive_directory = root.parent / ".archives"
        archive_directory.mkdir(parents=True, exist_ok=True)
        real_archive_directory = archive_directory.resolve(strict=True)
        real_archive_directory.relative_to(root.parent.resolve(strict=True))
        if archive_directory.is_symlink():
            raise OSError("Archive destination is a symbolic link")
        archived_original = _collision_free_path(
            real_archive_directory, archive_path.name
        )
        if archived_original.exists():
            raise OSError("Archive destination already exists")
        _move_without_overwrite(archive_path, archived_original)
        try:
            if final_target.exists():
                raise OSError("Game destination already exists")
            _move_without_overwrite(temporary_path, final_target)
            temporary_path = None
        except OSError:
            try:
                _move_without_overwrite(archived_original, original_path)
                archived_original = None
            except OSError:
                pass
            raise

        return {
            "name": final_target.name,
            "system": system,
            "console": console,
            "destination": str(final_target),
            "archive": str(archived_original),
        }
    except (
        OSError, RuntimeError, ValueError, zipfile.BadZipFile,
        zipfile.LargeZipFile, NotImplementedError, EOFError, KeyError,
    ):
        return None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass


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
            if downloads_resolved in (self.home, Path(downloads_resolved.anchor)):
                return []
            if root_resolved == self.home or root_resolved == Path(root_resolved.anchor):
                return []
            if downloads_resolved == root_resolved:
                return []
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

        recognized_suffixes = set(DESTINATION_BY_EXTENSION) | {".zip"}
        try:
            candidates = []
            with os.scandir(downloads_resolved) as entries:
                for entry in islice(entries, MAX_DOWNLOAD_DIRECTORY_ENTRIES):
                    if (
                        entry.name.startswith(".")
                        or entry.is_symlink()
                        or Path(entry.name).suffix.casefold() not in recognized_suffixes
                    ):
                        continue
                    candidates.append(entry)
                    if len(candidates) >= self.max_entries:
                        break
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
                is_zip_archive = path.suffix.casefold() == ".zip"
                destination = DESTINATION_BY_EXTENSION.get(path.suffix.casefold())
                if (
                    (destination is None and not is_zip_archive)
                    or not entry.is_file(follow_symlinks=False)
                ):
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

                if is_zip_archive:
                    organized = _extract_single_game_zip(
                        path, root_resolved, signature
                    )
                    if organized is not None:
                        self._observed.pop(key, None)
                        moved.append(organized)
                    continue

                if destination is None:
                    continue
                system, console = destination
                target_directory = root_resolved / system / console
                target_directory.mkdir(parents=True, exist_ok=True)
                real_target_directory = target_directory.resolve(strict=True)
                real_target_directory.relative_to(root_resolved)
                if target_directory.is_symlink():
                    continue
                target = _collision_free_path(real_target_directory, entry.name)
                # Link/unlink or a verified temporary copy preserves the source
                # until a no-overwrite destination has been created.
                if target.exists():
                    continue
                _move_without_overwrite(path, target, signature)
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
