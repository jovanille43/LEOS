"""Read-only gamepad navigation for the LEOS startup mode selector."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from controller_center.backend import GamepadBackend, backend_available
from controller_center.profiles import ControllerProfileStore, device_profile_id
from gaming.backend.gamepad import mapper_from_preferences, open_first_available_gamepad
from leos_core.settings import SettingsStore


class ModeSelectorController(QObject):
    """Expose local controller navigation without changing system input mapping."""

    gamepadAction = Signal(str)
    gamepadStatusChanged = Signal()
    onboardingChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._settings = SettingsStore()
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

    @Property(bool, notify=onboardingChanged)
    def themeSelectionComplete(self) -> bool:
        return bool(self._settings.get("theme_selection_complete", False))

    @Slot(result=bool)
    def completeThemeSelection(self) -> bool:
        """Remember the first-run theme choice without blocking session startup."""
        if self.themeSelectionComplete:
            return True
        try:
            self._settings.set("theme_selection_complete", True)
        except (OSError, ValueError, TypeError, KeyError):
            return False
        self.onboardingChanged.emit()
        return True

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
