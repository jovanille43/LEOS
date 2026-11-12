"""QObject bridge exposing Gaming services and local gamepad navigation."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QRunnable, QProcess, QThreadPool, QTimer, Signal, Slot

from controller_center.backend import GamepadBackend, backend_available
from controller_center.profiles import ControllerProfileStore, device_profile_id
from gaming.backend.gamepad import (
    GamepadActionMapper,
    mapper_from_preferences,
    open_first_available_gamepad,
)
from pathlib import Path

from desktop.notification_store import NotificationStore
from leos_core.settings import SettingsStore
from desktop.notifications import post_notification

from .library import GameLibraryModel
from .system_monitor import SystemMonitor
from .power_profiles import PowerProfileState, inspect_power_profiles, set_power_profile
from .mangohud import find_mangohud


class _PowerProfileTaskSignals(QObject):
    completed = Signal(object, bool, str)


class _PowerProfileTask(QRunnable):
    """Run slow power-profiles-daemon queries away from the QML thread."""

    def __init__(self, profile: str | None = None) -> None:
        super().__init__()
        self.profile = profile
        self.signals = _PowerProfileTaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            if self.profile is None:
                state = inspect_power_profiles()
                success, message = True, state.message
            else:
                success, message = set_power_profile(self.profile)
                state = inspect_power_profiles()
        except Exception:
            state = PowerProfileState(
                False, "", (), "Gestion native de l'énergie indisponible"
            )
            success, message = False, state.message
        self.signals.completed.emit(state, success, message)


class GamingController(QObject):
    messageChanged = Signal(str)
    desktopRequested = Signal()
    gamepadAction = Signal(str)
    gamepadStatusChanged = Signal()
    notificationCountChanged = Signal()
    notificationSettingsChanged = Signal()
    powerProfilesChanged = Signal()
    mangoHudChanged = Signal()
    launchStatusChanged = Signal()
    launcherStatusChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.library = GameLibraryModel()
        self._launcher_statuses = self.library.launcherStatuses()
        self._launcher_refresh_timer = QTimer(self)
        self._launcher_refresh_timer.setInterval(15000)
        self._launcher_refresh_timer.timeout.connect(self.refreshLauncherStatuses)
        self._launcher_refresh_timer.start()
        self.monitor = SystemMonitor()
        self._power_profiles = PowerProfileState(
            False, "", (), "Détection des profils d'énergie en cours…"
        )
        self._power_profile_message = self._power_profiles.message
        self._power_profile_task: _PowerProfileTask | None = None
        self._power_profile_refresh_timer = QTimer(self)
        self._power_profile_refresh_timer.setInterval(10000)
        self._power_profile_refresh_timer.timeout.connect(self.refreshPowerProfiles)
        self._power_profile_refresh_timer.start()
        QTimer.singleShot(0, self.refreshPowerProfiles)
        self.settings = SettingsStore()
        self._mangohud_path = find_mangohud()
        self._mangohud_enabled = bool(
            self.settings.get("gaming_mangohud_enabled", False)
        ) and bool(self._mangohud_path)
        self.notifications = NotificationStore()
        self._notification_refresh_timer = QTimer(self)
        self._notification_refresh_timer.setInterval(3000)
        self._notification_refresh_timer.timeout.connect(self.refreshNotificationCount)
        self._notification_refresh_timer.start()
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


    @Property(bool, constant=False)
    def animationsEnabled(self) -> bool:
        return bool(self.settings.get("animations_enabled", True))

    @Property(bool, constant=False)
    def soundsEnabled(self) -> bool:
        return bool(self.settings.get("sounds_enabled", True))

    @Property(str, notify=powerProfilesChanged)
    def activePowerProfile(self) -> str:
        return self._power_profiles.active

    @Property("QStringList", notify=powerProfilesChanged)
    def availablePowerProfiles(self) -> list[str]:
        return list(self._power_profiles.profiles)

    @Property(str, notify=powerProfilesChanged)
    def powerProfileStatus(self) -> str:
        return self._power_profile_message

    @Slot()
    def refreshPowerProfiles(self) -> None:
        if self._power_profile_task is not None:
            return
        self._start_power_profile_task(None)

    def _start_power_profile_task(self, profile: str | None) -> None:
        task = _PowerProfileTask(profile)
        task.signals.completed.connect(self._on_power_profile_task_completed)
        self._power_profile_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(object, bool, str)
    def _on_power_profile_task_completed(
        self, state: PowerProfileState, success: bool, message: str
    ) -> None:
        self._power_profile_task = None
        self._power_profiles = state
        self._power_profile_message = message or state.message
        self._message = self._power_profile_message
        self.messageChanged.emit(self._message)
        self.powerProfilesChanged.emit()

    @Slot(str, result=bool)
    def applyPowerProfile(self, profile: str) -> bool:
        if not isinstance(profile, str) or profile not in self._power_profiles.profiles:
            self._power_profile_message = "Ce profil n'est pas proposé par le système."
            self.powerProfilesChanged.emit()
            return False
        if self._power_profile_task is not None:
            self._power_profile_message = "Une opération de gestion d'énergie est déjà en cours."
            self.powerProfilesChanged.emit()
            return False
        self._power_profile_message = "Changement du profil d'énergie en cours…"
        self._message = self._power_profile_message
        self.powerProfilesChanged.emit()
        self.messageChanged.emit(self._message)
        self._start_power_profile_task(profile)
        return True

    @Property(str, notify=launchStatusChanged)
    def lastLaunchStatus(self) -> str:
        return self.library.lastLaunchStatus

    @Property("QStringList", notify=launcherStatusChanged)
    def launcherStatuses(self) -> list[str]:
        return list(self._launcher_statuses)

    @Slot()
    def refreshLauncherStatuses(self) -> None:
        statuses = self.library.launcherStatuses()
        if statuses != self._launcher_statuses:
            self._launcher_statuses = statuses
            self.launcherStatusChanged.emit()

    @Property(bool, notify=mangoHudChanged)
    def mangoHudAvailable(self) -> bool:
        return bool(self._mangohud_path)

    @Property(bool, notify=mangoHudChanged)
    def mangoHudEnabled(self) -> bool:
        return self._mangohud_enabled

    @Slot(bool, result=bool)
    def setMangoHudEnabled(self, enabled: bool) -> bool:
        if enabled and not self._mangohud_path:
            self._mangohud_enabled = False
            self.mangoHudChanged.emit()
            return False
        requested = bool(enabled)
        try:
            self.settings.set("gaming_mangohud_enabled", requested)
        except (OSError, ValueError, TypeError):
            self._message = "Impossible d'enregistrer le réglage MangoHud."
            self.messageChanged.emit(self._message)
            return False
        self._mangohud_enabled = requested
        self.mangoHudChanged.emit()
        return self._mangohud_enabled

    @Property(int, notify=notificationCountChanged)
    def unreadNotificationCount(self) -> int:
        return self.notifications.unread_count()

    @Property(bool, notify=notificationSettingsChanged)
    def silentNotificationsInGaming(self) -> bool:
        return bool(self.settings.get("silent_notifications_in_gaming", True))

    @Slot(result=bool)
    def toggleSilentNotifications(self) -> bool:
        enabled = not self.silentNotificationsInGaming
        try:
            self.settings.set("silent_notifications_in_gaming", enabled)
        except (OSError, ValueError, TypeError):
            self._message = "Impossible d'enregistrer le réglage des notifications."
            self.messageChanged.emit(self._message)
            return not enabled
        self.notificationSettingsChanged.emit()
        return enabled

    @Slot()
    def refreshNotificationCount(self) -> None:
        if self.notifications.load():
            self.notificationCountChanged.emit()

    @Slot(result=bool)
    def openControllerCenter(self) -> bool:
        """Open the dedicated controller configuration window from Gaming Mode."""
        entry = Path(__file__).resolve().parents[2] / "controller_center" / "main.py"
        if not entry.is_file():
            self._message = "Le Centre des manettes LEOS est introuvable sur cette installation."
            self.messageChanged.emit(self._message)
            return False
        result = QProcess.startDetached("python3", [str(entry)], str(Path.home()))
        opened = bool(result[0] if isinstance(result, tuple) else result)
        if not opened:
            self._message = "Impossible d’ouvrir le Centre des manettes LEOS."
            self.messageChanged.emit(self._message)
        return opened

    @Slot(result=bool)
    def openNotificationCentre(self) -> bool:
        entry = Path(__file__).resolve().parents[2] / "desktop" / "notifications_main.py"
        if not entry.is_file():
            return False
        result = QProcess.startDetached("python3", [str(entry)], str(Path.home()))
        return bool(result[0] if isinstance(result, tuple) else result)

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
            self._gamepad_mapper.reset()
            self._gamepad_path = ""
            self._set_gamepad_status("Manette : backend indisponible")
            return

        devices = self._gamepad.scan()
        paths = {item["path"] for item in devices}
        if self._gamepad_path and self._gamepad_path not in paths:
            self._gamepad.close()
            self._gamepad_mapper.reset()
            self._gamepad_path = ""

        if not self._gamepad_path and devices:
            candidate, error = open_first_available_gamepad(self._gamepad, devices)
            if candidate is not None:
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
            else:
                self._set_gamepad_status(
                    f"Manettes détectées, lecture impossible : {error}"
                    if error else "Aucune manette accessible"
                )
        elif not devices:
            self._set_gamepad_status("Manette non détectée · clavier/souris disponibles")

    def _poll_gamepad(self) -> None:
        for event in self._gamepad.poll():
            action = self._gamepad_mapper.feed(event)
            if action:
                self.gamepadAction.emit(action)
        if self._gamepad_path and self._gamepad.device is None:
            self._gamepad_path = ""
            self._gamepad_mapper.reset()
            self._set_gamepad_status("Connexion manette interrompue — nouvelle détection…")
            return
        repeated_action = self._gamepad_mapper.repeat_action()
        if repeated_action:
            self.gamepadAction.emit(repeated_action)

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

    @Slot(int, bool, result=bool)
    def launchGame(self, row: int, mango_hud: bool = False) -> bool:
        launched = self.library.launchGame(
            row, mango_hud=bool(mango_hud and self._mangohud_enabled)
        )
        self._message = self.library.lastLaunchStatus
        self.messageChanged.emit(self._message)
        self.launchStatusChanged.emit()
        if not launched:
            post_notification(
                "Lancement de jeu impossible",
                self.library.lastLaunchStatus,
                "error",
                native=False,
            )
        return launched

    def shutdown(self) -> None:
        self.monitor.stop()
        self._notification_refresh_timer.stop()
        self._launcher_refresh_timer.stop()
        self._power_profile_refresh_timer.stop()
        self._gamepad_poll_timer.stop()
        self._gamepad_refresh_timer.stop()
        self._gamepad.close()

    @Slot()
    def returnToDesktop(self) -> None:
        try:
            self.settings.set("last_mode", "desktop")
        except (OSError, ValueError, TypeError, KeyError):
            message = (
                "Retour vers le bureau KDE demandé. "
                "Le choix de démarrage n'a pas pu être mémorisé."
            )
            level = "warning"
        else:
            message = "Retour vers le bureau KDE demandé."
            level = "info"

        try:
            post_notification("Retour à Desktop Mode", message, level, native=False)
        finally:
            # Returning to KDE is the requested action; neither a preference
            # write nor best-effort notification storage may block it.
            self.desktopRequested.emit()
