"""Private, bounded local notification inbox for LEOS-owned events."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from leos_core.paths import state_home as xdg_state_home

MAX_NOTIFICATIONS = 100
MAX_NOTIFICATION_FILE_BYTES = 512 * 1024
MAX_TITLE = 160
MAX_BODY = 2000

LEVELS = {"info", "success", "warning", "error"}


def _store_path() -> Path:
    root = xdg_state_home()
    return root / "leos" / "notifications.json"


def _valid_record(item: object) -> bool:
    if not isinstance(item, dict) or set(item) != {"id", "title", "body", "level", "created_at", "read"}:
        return False
    try:
        uuid.UUID(item["id"])
        datetime.fromisoformat(item["created_at"])
    except (ValueError, TypeError, AttributeError):
        return False
    return (
        isinstance(item["title"], str) and 0 < len(item["title"]) <= MAX_TITLE
        and isinstance(item["body"], str) and len(item["body"]) <= MAX_BODY
        and isinstance(item["level"], str) and item["level"] in LEVELS
        and type(item["read"]) is bool
    )


class NotificationStore:
    """Atomic JSON inbox. It stores LEOS notifications, not the KDE system history."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _store_path()
        self._items: list[dict] = []
        self.load()

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.parent.is_symlink():
            raise OSError("Notification history directory cannot be a symbolic link")
        lock_path = self.path.with_name(self.path.name + ".lock")
        if lock_path.is_symlink():
            raise OSError("Notification history lock cannot be a symbolic link")
        with lock_path.open("a", encoding="utf-8") as lock:
            os.chmod(lock_path, 0o600)
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def load(self) -> bool:
        # Never retain stale in-memory events after a file is removed, replaced,
        # corrupt, or exceeds the bounded on-disk format.
        self._items = []
        if self.path.is_symlink() or self.path.parent.is_symlink():
            return False
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_NOTIFICATION_FILE_BYTES + 1)
            if len(raw) > MAX_NOTIFICATION_FILE_BYTES:
                return False
            data = json.loads(raw.decode("utf-8"))
        except FileNotFoundError:
            return True
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        if (isinstance(data, dict) and type(data.get("schema_version")) is int
                and data.get("schema_version") == 1
                and isinstance(data.get("items"), list)
                and len(data["items"]) <= MAX_NOTIFICATIONS
                and all(_valid_record(x) for x in data["items"])
                and len({x["id"] for x in data["items"]}) == len(data["items"])):
            self._items = list(data["items"])
            return True
        return False

    def items(self, unread_only: bool = False) -> list[dict]:
        self.load()
        records = self._items
        if unread_only:
            records = [x for x in records if not x["read"]]
        return [dict(x) for x in reversed(records)]

    def unread_count(self) -> int:
        self.load()
        return sum(not x["read"] for x in self._items)

    def add(self, title: str, body: str = "", level: str = "info") -> str:
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > MAX_TITLE:
            raise ValueError("Invalid notification title")
        if not isinstance(body, str) or len(body) > MAX_BODY:
            raise ValueError("Invalid notification body")
        if not isinstance(level, str) or level not in LEVELS:
            raise ValueError("Invalid notification level")
        record = {
            "id": str(uuid.uuid4()), "title": title.strip(), "body": body,
            "level": level, "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
        }
        with self._exclusive_lock():
            if not self.load():
                raise OSError("Notification history is invalid or inaccessible")
            self._items.append(record)
            self._items = self._items[-MAX_NOTIFICATIONS:]
            self.save()
        return record["id"]

    def mark_read(self, notification_id: str) -> bool:
        with self._exclusive_lock():
            if not self.load():
                return False
            for item in self._items:
                if item["id"] == notification_id:
                    if not item["read"]:
                        item["read"] = True
                        self.save()
                    return True
        return False

    def dismiss(self, notification_id: str) -> bool:
        with self._exclusive_lock():
            if not self.load():
                return False
            before = len(self._items)
            self._items = [x for x in self._items if x["id"] != notification_id]
            if len(self._items) == before:
                return False
            self.save()
            return True

    def mark_all_read(self) -> None:
        with self._exclusive_lock():
            if not self.load():
                return
            changed = False
            for item in self._items:
                if not item["read"]:
                    item["read"] = True
                    changed = True
            if changed:
                self.save()

    def clear(self) -> None:
        with self._exclusive_lock():
            if not self.load():
                return
            if self._items:
                self._items = []
                self.save()

    def save(self) -> None:
        """Atomically persist the in-memory snapshot; callers hold _exclusive_lock."""
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise OSError("Notification history path cannot be a symbolic link")
        payload = json.dumps({"schema_version": 1, "items": self._items},
                             ensure_ascii=False, indent=2) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        fd, temporary = tempfile.mkstemp(prefix="notifications.", suffix=".tmp",
                                         dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
