"""Per-user LEOS download organizer, started by the KDE session."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gaming.backend.download_organizer import DownloadOrganizer


POLL_INTERVAL_SECONDS = 10


def _acquire_lock():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    if runtime.is_symlink() or not runtime.is_dir():
        return None
    lock_path = runtime / "leos-download-organizer.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return descriptor
    except (OSError, BlockingIOError):
        try:
            os.close(descriptor)
        except (OSError, UnboundLocalError):
            pass
        return None


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
    organizer = DownloadOrganizer()
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
