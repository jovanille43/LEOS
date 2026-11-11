"""QObject bridge exposing Gaming services and local gamepad navigation."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from controller_center.backend import GamepadBackend, backend_available
from controller_center.profiles import ControllerProfileStore, device_profile_id
from gaming.backend.gamepad import GamepadActionMapper, mapper_from_preferences
from leos_core.settings import SettingsStore

from .library import GameLibraryModel
from .system_monitor import SystemMonitor


class GamingController(QObject):
    messageChanged = Signal(str)
    desktopRequested = Signal()
    gamepadAction = Signal(str)
    gamepadStatusChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.library = GameLibraryModel()
        self.monitor = SystemMonitor()
        self.settings = SettingsStore()
        self._message = ""
        self._gamepad = GamepadBackend()
        self._gamepad_mapper = GamepadActionMapper()
        self._controller_profiles = ControllerProfileStore()
        self._gamepad_path = ""
        self._gamepad_status = (
            "Détection des manettes active"
            if backend_available()
            else "Manette : backend indisponible"
        )

        self._gamepad_poll_timer = QTimer(self)
        self._gamepad_poll_timer.setInterval(25)
        self._gamepad_poll_timer.timeout.connect(self._poll_gamepad)
        self._gamepad_refresh_timer = QTimer(self)
        self._gamepad_refresh_timer.setInterval(2500)
        self._gamepad_refresh_timer.timeout.connect(self._refresh_gamepad)
        self._refresh_gamepad()
        self._gamepad_poll_timer.start()
        self._gamepad_refresh_timer.start()

    @Property(str, notify=gamepadStatusChanged)
    def gamepadStatus(self) -> str:
        return self._gamepad_status

    def _set_gamepad_status(self, message: str) -> None:
        if self._gamepad_status != message:
            self._gamepad_status = message
            self.gamepadStatusChanged.emit()

    def _refresh_gamepad(self) -> None:
        if not backend_available():
            self._gamepad.close()
            self._gamepad_path = ""
            self._set_gamepad_status("Manette : backend indisponible")
            return

        devices = self._gamepad.scan()
        paths = {item["path"] for item in devices}
        if self._gamepad_path and self._gamepad_path not in paths:
            self._gamepad.close()
            self._gamepad_path = ""

        if not self._gamepad_path and devices:
            candidate = devices[0]
            try:
                self._gamepad.open(candidate["path"])
                self._gamepad_path = candidate["path"]
                profile_id = device_profile_id(
                    candidate["name"],
                    candidate["vendor"],
                    candidate["product"],
                    candidate["phys"],
                    candidate["uniq"],
                    candidate["path"],
                )
                preferences = self._controller_profiles.get(profile_id)
                self._gamepad_mapper = mapper_from_preferences(preferences, candidate)
                self._set_gamepad_status(f"Manette : {candidate['name']}")
            except (OSError, ValueError):
                self._gamepad.close()
                self._set_gamepad_status("Manette détectée, lecture non autorisée")
        elif not devices:
            self._set_gamepad_status("Manette non détectée · clavier/souris disponibles")

    def _poll_gamepad(self) -> None:
        for event in self._gamepad.poll():
            action = self._gamepad_mapper.feed(event)
            if action:
                self.gamepadAction.emit(action)
        if self._gamepad_path and self._gamepad.device is None:
            self._gamepad_path = ""
            self._set_gamepad_status("Connexion manette interrompue — nouvelle détection…")

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
        self._message = (
            ""
            if launched
            else "Impossible d'ouvrir ce jeu avec sa configuration actuelle."
        )
        self.messageChanged.emit(self._message)
        return launched

    def shutdown(self) -> None:
        self._gamepad_poll_timer.stop()
        self._gamepad_refresh_timer.stop()
        self._gamepad.close()

    @Slot()
    def returnToDesktop(self) -> None:
        self.settings.set("last_mode", "desktop")
        self.desktopRequested.emit()
