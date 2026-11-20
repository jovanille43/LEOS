"""Read-only gamepad navigation for the LEOS startup mode selector."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from controller_center.backend import GamepadBackend, backend_available
from controller_center.profiles import ControllerProfileStore, device_profile_id
from gaming.backend.gamepad import mapper_from_preferences, open_first_available_gamepad
from leos_core.settings import SettingsStore
from desktop.first_run_appearance import DesktopAppearanceSetup


class _AppearanceSetupSignals(QObject):
    finished = Signal(bool, str)


class _AppearanceSetupTask(QRunnable):
    """Apply the consented Desktop profile without blocking the mode selector."""

    def __init__(self, settings: SettingsStore) -> None:
        super().__init__()
        self.settings = settings
        self.signals = _AppearanceSetupSignals()

    @Slot()
    def run(self) -> None:
        try:
            message = DesktopAppearanceSetup(settings=self.settings).apply()
        except Exception as error:
            self.signals.finished.emit(False, str(error))
        else:
            self.signals.finished.emit(True, message)


class ModeSelectorController(QObject):
    """Expose local controller navigation without changing system input mapping."""

    gamepadAction = Signal(str)
    gamepadStatusChanged = Signal()
    onboardingChanged = Signal()
    appearanceSetupChanged = Signal()
    appearanceSetupFinished = Signal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = SettingsStore()
        self._appearance_task: _AppearanceSetupTask | None = None
        self._appearance_setup_running = False
        self._backend = GamepadBackend()
        self._profiles = ControllerProfileStore()
        self._mapper = mapper_from_preferences({"profile": "auto"})
        self._device_path = ""
        self._gamepad_status = (
            "Manette : recherche en cours…"
            if backend_available()
            else "Manette : clavier et souris disponibles"
        )

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(25)
        self._poll_timer.timeout.connect(self._poll)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2500)
        self._refresh_timer.timeout.connect(self._refresh)

        self._refresh()
        self._refresh_timer.start()

    @Property(bool, constant=False)
    def animationsEnabled(self) -> bool:
        return bool(self._settings.get("animations_enabled", True))

    @Property(bool, constant=False)
    def soundsEnabled(self) -> bool:
        return bool(self._settings.get("sounds_enabled", True))

    @Property(bool, notify=onboardingChanged)
    def onboardingComplete(self) -> bool:
        return bool(self._settings.get("onboarding_complete", False))

    @Property(str, notify=appearanceSetupChanged)
    def desktopAppearanceStatus(self) -> str:
        return str(self._settings.get("desktop_appearance_setup", "pending"))

    @Property(bool, notify=appearanceSetupChanged)
    def appearanceSetupRunning(self) -> bool:
        return self._appearance_setup_running

    @Slot(result=bool)
    def beginDesktopAppearanceSetup(self) -> bool:
        """Start the backed-up, consented Desktop appearance transaction."""
        if self._appearance_setup_running or self.desktopAppearanceStatus != "pending":
            return False
        task = _AppearanceSetupTask(self._settings)
        task.signals.finished.connect(self._on_desktop_appearance_setup_finished)
        self._appearance_task = task
        self._appearance_setup_running = True
        self.appearanceSetupChanged.emit()
        QThreadPool.globalInstance().start(task)
        return True

    @Slot(result=bool)
    def skipDesktopAppearance(self) -> bool:
        """Remember that the user chose to keep their current KDE appearance."""
        if self._appearance_setup_running:
            return False
        try:
            DesktopAppearanceSetup(settings=self._settings).skip()
        except (OSError, ValueError, TypeError, KeyError, RuntimeError):
            return False
        self.appearanceSetupChanged.emit()
        return True

    @Slot(bool, str)
    def _on_desktop_appearance_setup_finished(self, succeeded: bool, message: str) -> None:
        self._appearance_setup_running = False
        self._appearance_task = None
        self.appearanceSetupChanged.emit()
        self.appearanceSetupFinished.emit(succeeded, message)

    @Slot(result=bool)
    def completeOnboarding(self) -> bool:
        """Remember that the user has seen the first-run LEOS introduction."""
        if self.onboardingComplete:
            return True
        try:
            self._settings.set("onboarding_complete", True)
        except (OSError, ValueError, TypeError, KeyError):
            return False
        self.onboardingChanged.emit()
        return True

    @Property(str, notify=gamepadStatusChanged)
    def gamepadStatus(self) -> str:
        return self._gamepad_status

    def _set_status(self, message: str) -> None:
        if self._gamepad_status != message:
            self._gamepad_status = message
            self.gamepadStatusChanged.emit()

    def _refresh(self) -> None:
        if not backend_available():
            self._backend.close()
            self._device_path = ""
            self._poll_timer.stop()
            self._set_status("Manette : clavier et souris disponibles")
            return

        devices = self._backend.scan()
        paths = {item["path"] for item in devices}
        if self._device_path and self._device_path not in paths:
            self._backend.close()
            self._device_path = ""
            self._poll_timer.stop()

        if not self._device_path and devices:
            # DRM/evdev enumeration can list an event node that is no longer
            # readable. Try every detected controller before falling back to
            # keyboard and mouse, rather than letting the first node block all.
            device, _open_error = open_first_available_gamepad(self._backend, devices)
            if device is None:
                self._backend.close()
                self._device_path = ""
                self._poll_timer.stop()
                self._set_status("Manette détectée, aucune accessible · clavier/souris disponibles")
                return
            try:
                profile_id = device_profile_id(
                    device["name"],
                    device["vendor"],
                    device["product"],
                    device["phys"],
                    device["uniq"],
                    device["path"],
                )
                preferences = self._profiles.get(profile_id)
                mapper = mapper_from_preferences(preferences, device)
                self._device_path = device["path"]
                self._mapper = mapper
                self._poll_timer.start()
                self._set_status(f"Manette connectée : {device['name']}")
            except (OSError, ValueError, TypeError, KeyError, RuntimeError):
                self._backend.close()
                self._device_path = ""
                self._poll_timer.stop()
                self._set_status("Manette détectée, lecture indisponible · clavier/souris disponibles")
        elif not devices:
            self._set_status("Manette non détectée · clavier/souris disponibles")

    def _poll(self) -> None:
        for event in self._backend.poll():
            action = self._mapper.feed(event)
            if action:
                self.gamepadAction.emit(action)

        if self._device_path and self._backend.device is None:
            self._device_path = ""
            self._poll_timer.stop()
            self._set_status("Manette déconnectée · nouvelle détection…")

    def shutdown(self) -> None:
        self._poll_timer.stop()
        self._refresh_timer.stop()
        self._backend.close()
