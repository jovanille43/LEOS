"""Qt bridge for the LEOS controller center."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from controller_center.backend import GamepadBackend, backend_available
from controller_center.input_state import ControllerInputState
from controller_center.profiles import (
    ControllerProfileStore,
    detect_controller_profile,
    device_profile_id,
)


PROFILE_LABELS = {
    "auto": "Automatique",
    "standard": "Standard",
    "xbox": "Xbox",
    "playstation": "PlayStation",
    "nintendo": "Nintendo",
    "custom": "Personnalisé",
}


class ControllerCenterController(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.backend = GamepadBackend()
        self.input_state = ControllerInputState()
        self.store = ControllerProfileStore()
        self.devices: list[dict] = []
        self.selected_index = -1
        self.selected_id = ""
        self.last_event = "Appuie sur un bouton ou déplace un stick."
        self.status = (
            "Recherche des manettes…"
            if backend_available()
            else "Module evdev indisponible. La détection sera activée après son installation."
        )
        self.buttons_text = "Aucun bouton maintenu."
        self.axes_text = "Aucun axe détecté pour le moment."
        self._profile = "auto"
        self._deadzone = 8

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(35)
        self.poll_timer.timeout.connect(self._poll)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3000)
        self.refresh_timer.timeout.connect(self.refreshDevices)

        self.refreshDevices()
        self.refresh_timer.start()

    @Property(bool, notify=changed)
    def backendAvailable(self) -> bool:
        return backend_available()

    @Property(list, notify=changed)
    def deviceNames(self) -> list[str]:
        return [item["name"] for item in self.devices]

    @Property(int, notify=changed)
    def selectedIndex(self) -> int:
        return self.selected_index

    @Property(str, notify=changed)
    def selectedDeviceName(self) -> str:
        if 0 <= self.selected_index < len(self.devices):
            return str(self.devices[self.selected_index]["name"])
        return "Aucune manette sélectionnée"

    @Property(str, notify=changed)
    def statusText(self) -> str:
        return self.status

    @Property(str, notify=changed)
    def lastEventText(self) -> str:
        return self.last_event

    @Property(str, notify=changed)
    def buttonsText(self) -> str:
        return self.buttons_text

    @Property(str, notify=changed)
    def axesText(self) -> str:
        return self.axes_text

    @Property(str, notify=changed)
    def profileName(self) -> str:
        return PROFILE_LABELS[self._profile]


    @Property(str, notify=changed)
    def profileHint(self) -> str:
        if self._profile != "auto":
            return "Profil choisi manuellement"
        if not 0 <= self.selected_index < len(self.devices):
            return "Détection automatique à la connexion"
        item = self.devices[self.selected_index]
        detected = detect_controller_profile(item["name"], item["vendor"], item["product"])
        return (
            f"Profil détecté : {PROFILE_LABELS[detected]}"
            if detected
            else "Manette non reconnue — disposition standard utilisée"
        )

    @Property(int, notify=changed)
    def deadzone(self) -> int:
        return self._deadzone

    @Slot()
    def refreshDevices(self) -> None:
        previous = self.selected_id
        self.devices = self.backend.scan() if backend_available() else []
        self.selected_index = next(
            (i for i, item in enumerate(self.devices)
             if device_profile_id(**self._identity_args(item)) == previous),
            0 if self.devices else -1,
        )
        if previous and self.selected_index >= 0:
            current = device_profile_id(**self._identity_args(self.devices[self.selected_index]))
            if current != previous:
                self._close_monitor()
        elif not self.devices:
            self._close_monitor()

        if self.selected_index >= 0:
            self._select_current(open_device=not self.poll_timer.isActive())
            self.status = f"{len(self.devices)} manette(s) détectée(s)."
        elif backend_available():
            self.status = "Aucune manette détectée. Branche ou connecte une manette."
            self.selected_id = ""
        self.changed.emit()

    @staticmethod
    def _identity_args(item: dict) -> dict:
        return {
            "name": item["name"],
            "vendor": item["vendor"],
            "product": item["product"],
            "phys": item["phys"],
            "uniq": item["uniq"],
            "fallback_path": item["path"],
        }

    @Slot(int)
    def selectDevice(self, index: int) -> None:
        if not 0 <= index < len(self.devices):
            return
        self._close_monitor()
        self.selected_index = index
        self._select_current(open_device=True)
        self.changed.emit()

    def _select_current(self, open_device: bool) -> None:
        item = self.devices[self.selected_index]
        self.selected_id = device_profile_id(**self._identity_args(item))
        record = self.store.get(self.selected_id)
        self._profile = record["profile"]
        self._deadzone = record["deadzone"]
        self.axes_text = ", ".join(item["axes"]) or "Aucun axe analogique"
        if open_device:
            try:
                self.backend.open(item["path"])
                self.poll_timer.start()
                self.status = "Manette connectée — test des boutons actif."
            except (OSError, ValueError) as error:
                self.status = f"Manette détectée, mais lecture impossible : {error}"
                self.poll_timer.stop()

    def _poll(self) -> None:
        events = self.backend.poll()
        if self.backend.device is None and self.poll_timer.isActive():
            self.poll_timer.stop()
            self.input_state.clear()
            self.buttons_text = self.input_state.buttons_text
            self.status = "Connexion interrompue — nouvelle détection en cours…"
            self.changed.emit()
        if not events:
            return
        for event in events:
            description = self.input_state.consume(event)
            if description:
                self.last_event = description
        self.buttons_text = self.input_state.buttons_text
        if self.backend.axes:
            self.axes_text = " · ".join(
                f"{name}: {value}" for name, value in self.backend.axes.items()
            )
        self.changed.emit()

    @Slot(str)
    def setProfile(self, profile: str) -> None:
        reverse = {label: key for key, label in PROFILE_LABELS.items()}
        key = profile if profile in PROFILE_LABELS else reverse.get(profile, "")
        if not key or not self.selected_id:
            return
        self._profile = key
        self._save_preferences()
        self.changed.emit()

    @Slot(int)
    def setDeadzone(self, value: int) -> None:
        self._deadzone = max(0, min(40, int(value)))
        self._save_preferences()
        self.changed.emit()

    @Slot()
    def saveStickCenter(self) -> None:
        if not self.selected_id or not self.backend.axes:
            self.status = "Déplace les sticks ou sélectionne une manette avant le calibrage."
            self.changed.emit()
            return
        self.store.update(
            self.selected_id,
            axis_centers={name: int(value) for name, value in self.backend.axes.items()},
        )
        self.status = "Position neutre enregistrée dans ton profil LEOS."
        self.changed.emit()

    def _save_preferences(self) -> None:
        if self.selected_id:
            self.store.update(
                self.selected_id,
                profile=self._profile,
                deadzone=self._deadzone,
            )

    def _close_monitor(self) -> None:
        self.poll_timer.stop()
        self.backend.close()
        self.input_state.clear()
        self.buttons_text = self.input_state.buttons_text

    def shutdown(self) -> None:
        self.refresh_timer.stop()
        self._close_monitor()
