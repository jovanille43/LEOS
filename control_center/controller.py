"""QML bridge for LEOS preferences and native KDE settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QProcess, Signal, Slot

from control_center.settings_modules import general_settings_command, settings_module_command
from desktop.themes import palette_for_theme
from desktop.kde_colors import KdeColorSchemeManager
from desktop.plasma_style import PlasmaStyleManager
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_backup import PlasmaBackupManager
from desktop.plasma_inspector import inspect_plasma_config, build_layout_plan, format_layout_report
from gaming.backend.system_monitor import SystemMonitor
from leos_core.settings import SettingsStore
from desktop.notifications import post_notification
from control_center.system_updates import (
    interpret_update_check_exit_code,
    system_update_check_command,
    system_updater_command,
)


class ControlCenterController(QObject):
    settingsChanged = Signal()
    systemUpdatesChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self.desktopLayout = DesktopLayoutStore()
        self.plasmaBackups = PlasmaBackupManager()
        self.kdeColorSchemes = KdeColorSchemeManager()
        self.plasmaStyle = PlasmaStyleManager()
        self.monitor = SystemMonitor(self)
        self._system_update_status = "Aucune vérification lancée."
        self._system_update_check_running = False
        self._system_update_process = QProcess(self)
        self._system_update_process.finished.connect(self._on_system_update_check_finished)
        self._system_update_process.errorOccurred.connect(self._on_system_update_check_error)

    @Property(str, notify=systemUpdatesChanged)
    def systemUpdateStatus(self) -> str:
        return self._system_update_status

    @Property(bool, notify=systemUpdatesChanged)
    def systemUpdateCheckRunning(self) -> bool:
        return self._system_update_check_running

    @Property(bool, notify=systemUpdatesChanged)
    def systemUpdaterAvailable(self) -> bool:
        return system_updater_command() is not None

    def _set_system_update_status(self, message: str) -> None:
        self._system_update_status = message
        self.systemUpdatesChanged.emit()

    @Slot()
    def checkForSystemUpdates(self) -> None:
        if self._system_update_check_running:
            return
        command = system_update_check_command()
        if not command:
            message = "Vérification indisponible : uupd ou pkexec est introuvable."
            self._set_system_update_status(message)
            post_notification("Vérification des mises à jour indisponible", message, "warning")
            return
        self._system_update_process.setProgram(command[0])
        self._system_update_process.setArguments(command[1:])
        self._system_update_check_running = True
        self._set_system_update_status("Vérification en cours… Une autorisation système peut être demandée.")
        self._system_update_process.start()

    def _on_system_update_check_finished(self, exit_code: int, _exit_status) -> None:
        self._system_update_check_running = False
        result = interpret_update_check_exit_code(exit_code)
        if result == "available":
            message = "Une mise à jour système est disponible. Ouvre Bazzite Updater pour la consulter et choisir de l’installer."
            self._set_system_update_status(message)
            post_notification("Mise à jour système disponible", message, "warning")
        elif result == "up_to_date":
            self._set_system_update_status("Aucune mise à jour système disponible. Ton image est à jour.")
        elif result == "cancelled":
            self._set_system_update_status("Vérification annulée ou autorisation refusée.")
        else:
            detail = bytes(self._system_update_process.readAllStandardError()).decode("utf-8", errors="replace").strip()
            reason = detail.splitlines()[-1] if detail else "uupd a signalé une erreur."
            message = f"Impossible de vérifier les mises à jour : {reason}"
            self._set_system_update_status(message)
            post_notification("Échec de vérification des mises à jour", message, "error")
        self.systemUpdatesChanged.emit()

    def _on_system_update_check_error(self, _error) -> None:
        self._system_update_check_running = False
        message = "Impossible de démarrer uupd. Vérifie que Bazzite est correctement installé."
        self._set_system_update_status(message)
        post_notification("Vérification des mises à jour impossible", message, "error")

    @Slot(result=bool)
    def openSystemUpdater(self) -> bool:
        command = system_updater_command()
        if not command:
            self._set_system_update_status("Bazzite Updater n’est pas installé sur cette image.")
            return False
        opened = self._start_detached(command)
        if not opened:
            self._set_system_update_status("Impossible d’ouvrir Bazzite Updater.")
        return opened

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

    @Property(bool, notify=settingsChanged)
    def kdeColorSchemeToolAvailable(self) -> bool:
        return self.kdeColorSchemes.tool_available()

    @Property(str, notify=settingsChanged)
    def activeKdeColorScheme(self) -> str:
        return self.kdeColorSchemes.current_scheme() or "Inconnu"

    @Property(bool, notify=settingsChanged)
    def canRestoreKdeTheme(self) -> bool:
        return self.kdeColorSchemes.can_restore()

    @Property(bool, notify=settingsChanged)
    def plasmaStyleToolAvailable(self) -> bool:
        return self.plasmaStyle.tool_available()

    @Property(bool, notify=settingsChanged)
    def plasmaStyleInstalled(self) -> bool:
        return self.plasmaStyle.style_installed()

    @Property(str, notify=settingsChanged)
    def activePlasmaStyle(self) -> str:
        return self.plasmaStyle.current_style() or "Inconnu"

    @Property(bool, notify=settingsChanged)
    def canRestorePlasmaStyle(self) -> bool:
        return self.plasmaStyle.can_restore()

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

    @Slot(result=str)
    def applyKdeTheme(self) -> str:
        """Apply the currently selected LEOS colors after a confirmed UI action."""
        try:
            message = self.kdeColorSchemes.apply_theme(self.theme)
        except FileNotFoundError:
            message = "Outil KDE introuvable : le thème LEOS n'a pas été appliqué."
            post_notification("Thème KDE non appliqué", message, "error")
            return message
        except FileExistsError:
            message = "Un fichier de thème portant ce nom existe déjà ; il a été conservé."
            post_notification("Thème KDE non appliqué", message, "warning")
            return message
        except (OSError, RuntimeError, ValueError):
            message = "KDE n'a pas pu appliquer le thème. Le thème précédent reste récupérable."
            post_notification("Thème KDE non appliqué", message, "error")
            return message
        self.settingsChanged.emit()
        post_notification("Thème KDE appliqué", message, "success")
        return message

    @Slot(result=str)
    def restorePreviousKdeTheme(self) -> str:
        """Restore the non-LEOS color scheme captured before applying LEOS."""
        try:
            message = self.kdeColorSchemes.restore_previous_theme()
        except FileNotFoundError:
            message = "Aucun thème KDE précédent n'est enregistré."
            post_notification("Restauration du thème KDE impossible", message, "warning")
            return message
        except (OSError, RuntimeError, ValueError):
            message = "La restauration du thème KDE a échoué."
            post_notification("Restauration du thème KDE échouée", message, "error")
            return message
        self.settingsChanged.emit()
        post_notification("Thème KDE restauré", message, "success")
        return message

    @Slot(result=str)
    def applyPlasmaStyle(self) -> str:
        """Apply the LEOS Plasma Style only after explicit UI confirmation."""
        try:
            message = self.plasmaStyle.apply_style()
        except FileNotFoundError:
            message = "Style LEOS ou outil KDE introuvable : aucun changement appliqué."
            post_notification("Style Plasma non appliqué", message, "error")
            return message
        except (OSError, RuntimeError, ValueError):
            message = "Le style Plasma LEOS n'a pas pu être appliqué. Le thème précédent reste récupérable."
            post_notification("Style Plasma non appliqué", message, "error")
            return message
        self.settingsChanged.emit()
        post_notification("Style Plasma appliqué", message, "success")
        return message

    @Slot(result=str)
    def restorePreviousPlasmaStyle(self) -> str:
        """Restore the Plasma Style saved before the first LEOS application."""
        try:
            message = self.plasmaStyle.restore_previous_style()
        except FileNotFoundError:
            message = "Aucun style Plasma précédent n'est enregistré."
            post_notification("Restauration du style Plasma impossible", message, "warning")
            return message
        except (OSError, RuntimeError, ValueError):
            message = "La restauration du style Plasma a échoué."
            post_notification("Restauration du style Plasma échouée", message, "error")
            return message
        self.settingsChanged.emit()
        post_notification("Style Plasma restauré", message, "success")
        return message

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
            message = "Le fichier de disposition KDE est introuvable sur cette session."
            post_notification("Sauvegarde Plasma impossible", message, "warning")
            return message
        except (OSError, ValueError):
            message = "La sauvegarde Plasma n'a pas pu être créée."
            post_notification("Sauvegarde Plasma échouée", message, "error")
            return message
        self.settingsChanged.emit()
        message = f"Sauvegarde Plasma créée ({backup_id[:8]})."
        post_notification("Sauvegarde Plasma créée", message, "success")
        return message

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
