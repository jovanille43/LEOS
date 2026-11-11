"""Curated catalogue model; package availability is checked against Flatpak remotes."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QByteArray


class CatalogModel(QAbstractListModel):
    AppIdRole = int(Qt.ItemDataRole.UserRole) + 1
    NameRole = AppIdRole + 1
    CategoryRole = AppIdRole + 2
    DescriptionRole = AppIdRole + 3
    SourceRole = AppIdRole + 4
    CompatibilityRole = AppIdRole + 5
    OperationNoteRole = AppIdRole + 6
    InstalledRole = AppIdRole + 7

    ROLE_NAMES = {
        AppIdRole: QByteArray(b"appId"),
        NameRole: QByteArray(b"name"),
        CategoryRole: QByteArray(b"category"),
        DescriptionRole: QByteArray(b"description"),
        SourceRole: QByteArray(b"source"),
        CompatibilityRole: QByteArray(b"compatibility"),
        OperationNoteRole: QByteArray(b"operationNote"),
        InstalledRole: QByteArray(b"installed"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        catalog_path = Path(__file__).with_name("catalog.json")
        self._items = json.loads(catalog_path.read_text(encoding="utf-8"))
        self._installed: set[str] = set()

    def roleNames(self):
        return self.ROLE_NAMES

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        values = {
            self.AppIdRole: item["id"],
            self.NameRole: item["name"],
            self.CategoryRole: item["category"],
            self.DescriptionRole: item["description"],
            self.SourceRole: item["source"],
            self.CompatibilityRole: item["compatibility"],
            self.OperationNoteRole: item["operation_note"],
            self.InstalledRole: item["id"] in self._installed,
        }
        return values.get(role)

    def setInstalled(self, app_ids: set[str]) -> None:
        self._installed = app_ids
        if self._items:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._items) - 1, 0),
                [self.InstalledRole],
            )

    def itemAt(self, row: int) -> dict | None:
        if 0 <= row < len(self._items):
            return dict(self._items[row])
        return None
