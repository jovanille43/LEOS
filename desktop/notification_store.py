"""Private, bounded local notification inbox for LEOS-owned events."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

MAX_NOTIFICATIONS = 100
MAX_TITLE = 160
MAX_BODY = 2000
LEVELS = {"info", "success", "warning", "error"}


def _store_path() -> Path:
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
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

    def load(self) -> bool:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self._items = []
            return True
        except (OSError, json.JSONDecodeError):
            return False
        if (isinstance(data, dict) and data.get("schema_version") == 1
                and isinstance(data.get("items"), list)
                and len(data["items"]) <= MAX_NOTIFICATIONS
                and all(_valid_record(x) for x in data["items"])
                and len({x["id"] for x in data["items"]}) == len(data["items"])):
            self._items = list(data["items"])
            return True
        return False

    def items(self, unread_only: bool = False) -> list[dict]:
        records = self._items
        if unread_only:
            records = [x for x in records if not x["read"]]
        return [dict(x) for x in reversed(records)]

    def unread_count(self) -> int:
        return sum(not x["read"] for x in self._items)

    def add(self, title: str, body: str = "", level: str = "info") -> str:
        if not self.load():
            raise OSError("Notification history is invalid or inaccessible")
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
        self._items.append(record)
        self._items = self._items[-MAX_NOTIFICATIONS:]
        self.save()
        return record["id"]

    def mark_read(self, notification_id: str) -> bool:
        if not self.load():
            return False
        for item in self._items:
            if item["id"] == notification_id:
                item["read"] = True
                self.save()
                return True
        return False

    def dismiss(self, notification_id: str) -> bool:
        if not self.load():
            return False
        before = len(self._items)
        self._items = [x for x in self._items if x["id"] != notification_id]
        if len(self._items) == before:
            return False
        self.save()
        return True

    def mark_all_read(self) -> None:
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
        if not self.load():
            return
        if self._items:
            self._items = []
            self.save()

    def save(self) -> None:
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
