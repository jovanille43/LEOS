"""Per-user LEOS download organizer, started by the KDE session."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gaming.backend.download_organizer import (
    DownloadOrganizer,
    resolve_download_directory,
)


POLL_INTERVAL_SECONDS = 10


def resolve_leos_download_inbox(
    home: Path | None = None,
    config_home: Path | None = None,
) -> Path:
    """Use ~/Jeux by default while respecting an existing custom XDG folder."""
    base = Path(home or Path.home()).expanduser().resolve()
    if config_home is None:
        configured_home = os.environ.get("XDG_CONFIG_HOME", "")
        candidate_config = (
            Path(configured_home).expanduser()
            if configured_home
            else base / ".config"
        )
        config = candidate_config if candidate_config.is_absolute() else base / ".config"
    else:
        config = Path(config_home).expanduser()
        if not config.is_absolute():
            config = base / ".config"

    current = resolve_download_directory(base, config)
    inbox = base / "Jeux"
    standard_folders = {base / "Downloads", base / "Téléchargements"}
    if current == inbox or current not in standard_folders:
        return current

    updater = shutil.which("xdg-user-dirs-update")
    if not updater:
        return current
    try:
        result = subprocess.run(
            [updater, "--set", "DOWNLOAD", str(inbox)],
            check=False,
            timeout=5,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return current
    return inbox if result.returncode == 0 else current


def _acquire_lock():
    runtime_value = os.environ.get("XDG_RUNTIME_DIR", "")
    runtime = Path(runtime_value) if runtime_value else Path(f"/run/user/{os.getuid()}")
    if not runtime.is_absolute():
        return None

    runtime_descriptor = None
    descriptor = None
    try:
        directory_flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        runtime_descriptor = os.open(runtime, directory_flags)
        runtime_info = os.fstat(runtime_descriptor)
        if (
            not stat.S_ISDIR(runtime_info.st_mode)
            or runtime_info.st_uid != os.getuid()
            or runtime_info.st_mode & 0o077
        ):
            return None

        lock_flags = (
            os.O_CREAT
            | os.O_RDWR
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(
            "leos-download-organizer.lock",
            lock_flags,
            0o600,
            dir_fd=runtime_descriptor,
        )
        lock_info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(lock_info.st_mode)
            or lock_info.st_uid != os.getuid()
            or lock_info.st_nlink != 1
        ):
            return None

        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked_descriptor = descriptor
        descriptor = None
        return locked_descriptor
    except (OSError, ValueError, TypeError):
        return None
    finally:
        if runtime_descriptor is not None:
            try:
                os.close(runtime_descriptor)
            except OSError:
                pass
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _notify(moved: list[dict[str, str]]) -> None:
    notify_send = shutil.which("notify-send")
    if not notify_send or not moved:
        return
    by_console: dict[str, int] = {}
    for item in moved:
        label = f"{item['system']} · {item['console']}"
        by_console[label] = by_console.get(label, 0) + 1
    details = "\n".join(
        f"{label} : {count}" for label, count in sorted(by_console.items())
    )
    archived_zips = sum(1 for item in moved if item.get("archive"))
    if archived_zips:
        details += (
            f"\n{archived_zips} archive(s) ZIP originale(s) conservée(s) "
            "dans Emulation/.archives."
        )
    try:
        subprocess.run(
            [
                notify_send,
                "--app-name=LEOS",
                "--icon=applications-games",
                f"{len(moved)} jeu(x) rangé(s) automatiquement",
                details,
            ],
            check=False,
            timeout=3,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> int:
    lock = _acquire_lock()
    if lock is None:
        # Another session instance is already supervising Downloads, or the
        # per-user runtime directory is unavailable.
        return 0
    home = Path.home().expanduser().resolve()
    inbox = resolve_leos_download_inbox(home)
    try:
        if inbox.is_symlink():
            return 0
        inbox.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError:
        return 1
    organizer = DownloadOrganizer(downloads_dir=inbox, home=home)
    try:
        while True:
            try:
                moved = organizer.poll()
                _notify(moved)
            except Exception:
                # A temporary filesystem or metadata error must not terminate
                # the per-user service or interfere with the downloaded file.
                pass
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            fcntl.flock(lock, fcntl.LOCK_UN)
            os.close(lock)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
