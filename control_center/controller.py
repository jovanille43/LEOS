"""QML bridge for LEOS preferences and native KDE settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QProcess, Signal, Slot

from control_center.settings_modules import general_settings_command, settings_module_command
from desktop.themes import palette_for_theme
from gaming.backend.system_monitor import SystemMonitor
from leos_core.settings import SettingsStore


class ControlCenterController(QObject):
    settingsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self.monitor = SystemMonitor(self)

    @Property(bool, notify=settingsChanged)
    def animationsEnabled(self) -> bool:
        return bool(self.settings.get("animations_enabled"))

    @Property(bool, notify=settingsChanged)
    def soundsEnabled(self) -> bool:
        return bool(self.settings.get("sounds_enabled"))

    @Property(bool, notify=settingsChanged)
    def gamingOverlayEnabled(self) -> bool:
        return bool(self.settings.get("gaming_overlay_enabled"))

    @Property(str, notify=settingsChanged)
    def theme(self) -> str:
        return str(self.settings.get("theme"))

    @Property("QVariantMap", notify=settingsChanged)
    def themePalette(self) -> dict[str, str]:
        """Expose the selected palette to LEOS-owned QML without changing KDE."""
        return palette_for_theme(self.theme)

    @Property(str, notify=settingsChanged)
    def performanceProfile(self) -> str:
        return str(self.settings.get("performance_profile"))

    @Slot(bool)
    def setAnimationsEnabled(self, enabled: bool) -> None:
        self.settings.set("animations_enabled", enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setSoundsEnabled(self, enabled: bool) -> None:
        self.settings.set("sounds_enabled", enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setGamingOverlayEnabled(self, enabled: bool) -> None:
        self.settings.set("gaming_overlay_enabled", enabled)
        self.settingsChanged.emit()

    @Slot(str)
    def setTheme(self, theme: str) -> None:
        self.settings.set("theme", theme)
        self.settingsChanged.emit()

    @Slot(str)
    def setPerformanceProfile(self, profile: str) -> None:
        self.settings.set("performance_profile", profile)
        self.settingsChanged.emit()

    @Slot(str, result=bool)
    def openSettingsModule(self, section: str) -> bool:
        """Open one allowlisted KDE settings module without running a shell."""
        return self._start_detached(settings_module_command(section))

    @Slot(result=bool)
    def openAdvancedSettings(self) -> bool:
        """Open the complete KDE System Settings application."""
        return self._start_detached(general_settings_command())

    @staticmethod
    def _start_detached(command: list[str] | None) -> bool:
        if not command:
            return False
        process = QProcess()
        process.setProgram(command[0])
        process.setArguments(command[1:])
        return bool(process.startDetached())
