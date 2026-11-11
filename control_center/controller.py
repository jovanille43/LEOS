"""QML bridge for LEOS preferences and native KDE settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QProcess, Signal, Slot

from control_center.settings_modules import general_settings_command, settings_module_command
from desktop.themes import palette_for_theme
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_backup import PlasmaBackupManager
from desktop.plasma_inspector import inspect_plasma_config, build_layout_plan, format_layout_report
from gaming.backend.system_monitor import SystemMonitor
from leos_core.settings import SettingsStore


class ControlCenterController(QObject):
    settingsChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self.desktopLayout = DesktopLayoutStore()
        self.plasmaBackups = PlasmaBackupManager()
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

    @Property(str, notify=settingsChanged)
    def desktopLayoutProfile(self) -> str:
        return str(self.desktopLayout.get("profile"))

    @Property(bool, notify=settingsChanged)
    def dockEnabled(self) -> bool:
        return bool(self.desktopLayout.get("dock")["enabled"])

    @Property(str, notify=settingsChanged)
    def dockPosition(self) -> str:
        return str(self.desktopLayout.get("dock")["position"])

    @Property(str, notify=settingsChanged)
    def dockAlignment(self) -> str:
        return str(self.desktopLayout.get("dock")["alignment"])

    @Property(bool, notify=settingsChanged)
    def dockAutoHide(self) -> bool:
        return bool(self.desktopLayout.get("dock")["auto_hide"])

    @Property(bool, notify=settingsChanged)
    def desktopWidgetsEnabled(self) -> bool:
        return bool(self.desktopLayout.get("widgets_enabled"))

    @Property(bool, notify=settingsChanged)
    def plasmaConfigAvailable(self) -> bool:
        path = self.plasmaBackups.config_path
        return path.is_file() and not path.is_symlink()

    @Property(bool, notify=settingsChanged)
    def hasPlasmaBackup(self) -> bool:
        return self.plasmaBackups.latest_backup_id() is not None

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

    @Slot(str)
    def applyDesktopLayout(self, profile: str) -> None:
        self.desktopLayout.apply_profile(profile)
        self.settingsChanged.emit()

    @Slot(bool)
    def setDockEnabled(self, enabled: bool) -> None:
        self.desktopLayout.set_dock(enabled=enabled)
        self.settingsChanged.emit()

    @Slot(str)
    def setDockPosition(self, position: str) -> None:
        self.desktopLayout.set_dock(position=position)
        self.settingsChanged.emit()

    @Slot(str)
    def setDockAlignment(self, alignment: str) -> None:
        self.desktopLayout.set_dock(alignment=alignment)
        self.settingsChanged.emit()

    @Slot(bool)
    def setDockAutoHide(self, enabled: bool) -> None:
        self.desktopLayout.set_dock(auto_hide=enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setDesktopWidgetsEnabled(self, enabled: bool) -> None:
        self.desktopLayout.set_widgets_enabled(enabled)
        self.settingsChanged.emit()

    @Slot(result=str)
    def createPlasmaBackup(self) -> str:
        try:
            backup_id = self.plasmaBackups.create_backup()
        except FileNotFoundError:
            return "Le fichier de disposition KDE est introuvable sur cette session."
        except (OSError, ValueError):
            return "La sauvegarde Plasma n'a pas pu être créée."
        self.settingsChanged.emit()
        return f"Sauvegarde Plasma créée ({backup_id[:8]})."

    @Slot(result=str)
    def inspectPlasmaLayout(self) -> str:
        """Inspect the current KDE layout and return a non-mutating LEOS preview."""
        inspection = inspect_plasma_config(self.plasmaBackups.config_path)
        plan = build_layout_plan(self.desktopLayout.get(), inspection)
        return format_layout_report(inspection, plan)

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
