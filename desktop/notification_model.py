"""Qt model exposing the LEOS-owned notification inbox to QML."""
from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, Signal

from desktop.notification_store import NotificationStore

ROLES = {
    Qt.ItemDataRole.UserRole + 1: b"notificationId",
    Qt.ItemDataRole.UserRole + 2: b"title",
    Qt.ItemDataRole.UserRole + 3: b"body",
    Qt.ItemDataRole.UserRole + 4: b"level",
    Qt.ItemDataRole.UserRole + 5: b"createdAt",
    Qt.ItemDataRole.UserRole + 6: b"isRead",
}


class NotificationModel(QAbstractListModel):
    changed = Signal()

    def __init__(self, store: NotificationStore | None = None) -> None:
        super().__init__()
        self.store = store or NotificationStore()
        self._items = self.store.items()

    def roleNames(self):
        return ROLES

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        keys = {
            Qt.ItemDataRole.UserRole + 1: "id",
            Qt.ItemDataRole.UserRole + 2: "title",
            Qt.ItemDataRole.UserRole + 3: "body",
            Qt.ItemDataRole.UserRole + 4: "level",
            Qt.ItemDataRole.UserRole + 5: "created_at",
            Qt.ItemDataRole.UserRole + 6: "read",
        }
        if role == Qt.ItemDataRole.DisplayRole:
            return item["title"]
        key = keys.get(role)
        if key == "read":
            return item["read"]
        return item.get(key) if key else None

    def _reload(self):
        self.beginResetModel()
        self._items = self.store.items()
        self.endResetModel()
        self.changed.emit()

    @Slot(result=int)
    def unreadCount(self):
        return self.store.unread_count()

    @Slot(str, str, str, result=str)
    def addNotification(self, title: str, body: str, level: str = "info") -> str:
        try:
            identifier = self.store.add(title, body, level)
        except (OSError, ValueError):
            return ""
        self._reload()
        return identifier

    @Slot(str, result=bool)
    def markRead(self, notification_id: str) -> bool:
        result = self.store.mark_read(notification_id)
        if result:
            self._reload()
        return result

    @Slot(str, result=bool)
    def dismiss(self, notification_id: str) -> bool:
        result = self.store.dismiss(notification_id)
        if result:
            self._reload()
        return result

    @Slot()
    def markAllRead(self):
        self.store.mark_all_read()
        self._reload()

    @Slot()
    def clearAll(self):
        self.store.clear()
        self._reload()
