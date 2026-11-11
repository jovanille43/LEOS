"""Safe desktop application catalog and launcher for the LEOS menu."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot, Signal, Property, QTimer, QLocale

from desktop.desktop_entries import (
    desktop_entry_is_visible, filter_desktop_applications, localized_desktop_value,
)
from desktop.desktop_exec import parse_desktop_exec, resolve_desktop_working_directory
from desktop.dock_favourites import DockFavourites
from desktop.notification_store import NotificationStore
from desktop.recent_applications import RecentApplications


APP_DIRS = (
    Path("/usr/share/applications"),
    Path.home() / ".local/share/applications",
)
ROLE_NAMES = {
    Qt.ItemDataRole.UserRole + 1: b"name",
    Qt.ItemDataRole.UserRole + 2: b"desktopId",
    Qt.ItemDataRole.UserRole + 3: b"icon",
    Qt.ItemDataRole.UserRole + 4: b"category",
    Qt.ItemDataRole.UserRole + 5: b"description",
    Qt.ItemDataRole.UserRole + 6: b"isPinned",
}



class ApplicationCatalog(QAbstractListModel):
    """Read installed .desktop entries and launch them without a shell."""

    launchFailed = Signal(str)
    notificationCountChanged = Signal()
    categoryChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._all: list[dict[str, str]] = []
        self._visible: list[dict[str, str]] = []
        self._query = ""
        self._category = "Tout"
        self.favourites = DockFavourites()
        self.notifications = NotificationStore()
        self.recentApplications = RecentApplications()
        self._notification_timer = QTimer(self)
        self._notification_timer.setInterval(3000)
        self._notification_timer.timeout.connect(self.refreshNotificationCount)
        self._notification_timer.start()
        self.refresh()

    def roleNames(self):
        return ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._visible)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._visible):
            return None
        item = self._visible[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return item["name"]
        key = {
            Qt.ItemDataRole.UserRole + 1: "name",
            Qt.ItemDataRole.UserRole + 2: "desktopId",
            Qt.ItemDataRole.UserRole + 3: "icon",
            Qt.ItemDataRole.UserRole + 4: "category",
            Qt.ItemDataRole.UserRole + 5: "description",
        }.get(role)
        if role == Qt.ItemDataRole.UserRole + 6:
            return item["desktopId"] in self.favourites.items()
        return item.get(key, "") if key else None

    @staticmethod
    def _read_entry(path: Path) -> dict[str, str] | None:
        values: dict[str, str] = {}
        in_entry = False
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return None
        for line in lines:
            line = line.strip()
            if line == "[Desktop Entry]":
                in_entry = True
                continue
            if line.startswith("[") and line.endswith("]") and in_entry:
                break
            if in_entry and "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
        if values.get("Type") != "Application" or values.get("NoDisplay") == "true":
            return None
        if values.get("Hidden") == "true" or values.get("Name", "").startswith("_"):
            return None
        current_desktops = {
            item.strip().casefold()
            for item in os.environ.get("XDG_CURRENT_DESKTOP", "KDE").split(":")
            if item.strip()
        }
        if not desktop_entry_is_visible(values, current_desktops):
            return None
        # This first menu has no terminal emulator integration; do not expose
        # entries whose Desktop Entry explicitly requires a terminal window.
        if values.get("Terminal", "false").casefold() == "true":
            return None
        try:
            working_directory = resolve_desktop_working_directory(values.get("Path", ""))
        except ValueError:
            return None
        try_exec = values.get("TryExec", "").strip()
        if try_exec:
            if os.path.isabs(try_exec):
                if not Path(try_exec).is_file() or not os.access(try_exec, os.X_OK):
                    return None
            elif not shutil.which(try_exec):
                return None
        exec_line = values.get("Exec", "").strip()
        if not exec_line:
            return None
        locale_name = QLocale.system().name()
        return {
            "name": localized_desktop_value(values, "Name", locale_name) or path.stem,
            "desktopId": path.name,
            "icon": values.get("Icon", "application-x-executable"),
            "category": values.get("Categories", "Other;").split(";")[0] or "Other",
            "description": localized_desktop_value(values, "Comment", locale_name),
            "exec": exec_line,
            "path": str(path),
            "workingDirectory": working_directory,
        }

    @Slot()
    def refresh(self):
        found: dict[str, dict[str, str]] = {}
        for directory in APP_DIRS:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.desktop")):
                item = self._read_entry(path)
                if item:
                    found[item["desktopId"]] = item
        self._all = sorted(found.values(), key=lambda item: item["name"].casefold())
        self._apply_filter()

    def _apply_filter(self):
        selected = filter_desktop_applications(
            self._all,
            self._category,
            self.favourites.items(),
            self._query,
            self.recentApplications.items(),
        )
        self.beginResetModel()
        self._visible = selected
        self.endResetModel()

    @Slot(str)
    def setSearch(self, query: str):
        self._query = query.strip()
        self._apply_filter()

    @Property(str, notify=categoryChanged)
    def currentCategory(self) -> str:
        return self._category

    @Slot(str)
    def setCategory(self, category: str):
        if category not in self.categories():
            return
        if self._category == category:
            return
        self._category = category
        self._apply_filter()
        self.categoryChanged.emit()

    @Slot(result="QVariantList")
    def categories(self):
        return ["Tout", "Favoris", "Récemment utilisées"] + sorted({item["category"] for item in self._all})

    @Property(int, notify=notificationCountChanged)
    def unreadNotificationCount(self) -> int:
        return self.notifications.unread_count()

    @Slot()
    def refreshNotificationCount(self) -> None:
        if self.notifications.load():
            self.notificationCountChanged.emit()

    @Slot(result=int)
    def applicationCount(self):
        return len(self._all)

    @Slot(str, result=bool)
    def toggleFavourite(self, desktop_id: str) -> bool:
        if not any(item["desktopId"] == desktop_id for item in self._all):
            return False
        try:
            if desktop_id in self.favourites.items():
                self.favourites.unpin(desktop_id)
            else:
                self.favourites.pin(desktop_id)
        except (OSError, ValueError):
            return False
        self._apply_filter()
        return True


    @Slot(result=bool)
    def clearRecentApplications(self) -> bool:
        try:
            self.recentApplications.clear()
        except (OSError, ValueError):
            return False
        self._apply_filter()
        return True

    @Slot(str, result=bool)
    def launch(self, desktop_id: str) -> bool:
        item = next((entry for entry in self._all if entry["desktopId"] == desktop_id), None)
        if not item:
            self.launchFailed.emit("Cette application n'est plus disponible.")
            return False
        try:
            argv = parse_desktop_exec(
                item["exec"],
                name=item["name"],
                icon=item["icon"],
                desktop_file=item["path"],
            )
        except ValueError:
            self.launchFailed.emit("La commande de lancement de cette application est invalide.")
            return False
        if not argv:
            self.launchFailed.emit("Aucune commande de lancement disponible.")
            return False
        program = argv[0]
        args = argv[1:]
        if not os.path.isabs(program):
            resolved = shutil.which(program)
            if not resolved:
                self.launchFailed.emit("Le programme requis est introuvable.")
                return False
            program = resolved
        from PySide6.QtCore import QProcess
        result = QProcess.startDetached(program, args, item["workingDirectory"])
        ok = result[0] if isinstance(result, tuple) else result
        if not ok:
            self.launchFailed.emit("Impossible de démarrer cette application.")
            return False
        try:
            self.recentApplications.record(desktop_id)
        except (OSError, ValueError):
            # A history write failure must never turn a successful launch into a failure.
            pass
        self._apply_filter()
        return True
