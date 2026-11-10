"""Mode selection bridge shared by the LEOS session launcher and QML."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from leos_core.settings import SettingsStore


class ModeManager(QObject):
    modeRequested = Signal(str)
    statusChanged = Signal(str)

    def __init__(self, settings: SettingsStore | None = None) -> None:
        super().__init__()
        self.settings = settings or SettingsStore()
        self._status = ""

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(str, constant=False, notify=statusChanged)
    def lastMode(self) -> str:
        return str(self.settings.get("last_mode", "desktop"))

    @Slot(str)
    def requestMode(self, mode: str) -> None:
        if mode not in {"desktop", "gaming"}:
            self._status = "Mode LEOS inconnu."
            self.statusChanged.emit(self._status)
            return
        self.modeRequested.emit(mode)

    def setStatus(self, message: str) -> None:
        self._status = message
        self.statusChanged.emit(self._status)

    def rememberMode(self, mode: str) -> None:
        self.settings.set("last_mode", mode)
        self.statusChanged.emit(self._status)
