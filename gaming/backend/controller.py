"""QObject bridge exposing Gaming services to the QML interface."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from .library import GameLibraryModel
from .system_monitor import SystemMonitor


class GamingController(QObject):
    messageChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.library = GameLibraryModel()
        self.monitor = SystemMonitor()
        self._message = ""

    @Slot(str, str, str, result=bool)
    def addGame(self, title: str, platform: str, command: str) -> bool:
        added = self.library.addManualGame(title, platform, command)
        self._message = (
            "Jeu ajouté à la bibliothèque."
            if added
            else "Vérifie le nom et la commande de lancement."
        )
        self.messageChanged.emit(self._message)
        return added

    @Slot()
    def refreshLibrary(self) -> None:
        self.library.refresh()

    @Slot(int, result=bool)
    def launchGame(self, row: int) -> bool:
        launched = self.library.launchGame(row)
        self._message = "" if launched else "Impossible d'ouvrir ce jeu avec sa configuration actuelle."
        self.messageChanged.emit(self._message)
        return launched
