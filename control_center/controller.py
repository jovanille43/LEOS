"""QML bridge for LEOS preferences and native KDE settings."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QProcess, QRunnable, QThreadPool, QTimer, Signal, Slot

from control_center.settings_modules import general_settings_command, settings_module_command, system_monitor_command
from desktop.themes import palette_for_theme
from desktop.kde_colors import KdeColorSchemeManager
from desktop.plasma_style import PlasmaStyleManager
from desktop.layouts import DesktopLayoutStore
from desktop.plasma_backup import PlasmaBackupManager
from desktop.plasma_inspector import inspect_plasma_config, build_layout_plan, format_layout_report
from gaming.backend.system_monitor import SystemMonitor
from leos_core.settings import SettingsStore
from desktop.notifications import post_notification
from control_center.hardware import collect_hardware_snapshot
from control_center.network import collect_network_snapshot
from control_center.diagnostics import collect_system_diagnostics
from control_center.cleanup import collect_cleanup_preview
from control_center.system_updates import (
    interpret_update_check_exit_code,
    system_update_check_command,
    system_updater_command,
    pending_deployment_from_status,
    rpm_ostree_status_command,
)


SYSTEM_UPDATE_CHECK_TIMEOUT_MS = 120_000
DEPLOYMENT_STATUS_TIMEOUT_MS = 20_000


class _HardwareScanSignals(QObject):
    completed = Signal(dict)


class _HardwareScanTask(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = _HardwareScanSignals()

    @Slot()
    def run(self) -> None:
        try:
            snapshot = collect_hardware_snapshot()
        except Exception:
            # Always emit completion so the controller releases its in-flight
            # task slot and its normal timer can retry the scan later.
            self.signals.completed.emit({"_scan_error": "_HardwareScanTask"})
            return
        self.signals.completed.emit(snapshot)


class _NetworkScanSignals(QObject):
    completed = Signal(dict)


class _NetworkScanTask(QRunnable):
    def __init__(self, previous: dict[str, tuple[int, int]], elapsed: float) -> None:
        super().__init__()
        self.previous = previous
        self.elapsed = elapsed
        self.signals = _NetworkScanSignals()

    @Slot()
    def run(self) -> None:
        try:
            snapshot = collect_network_snapshot(self.previous, self.elapsed)
        except Exception:
            # Always emit completion so the controller releases its in-flight
            # task slot and its normal timer can retry the scan later.
            self.signals.completed.emit({"_scan_error": "_NetworkScanTask"})
            return
        self.signals.completed.emit(snapshot)


class _DiagnosticsScanTask(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = _HardwareScanSignals()

    @Slot()
    def run(self) -> None:
        try:
            snapshot = collect_system_diagnostics()
        except Exception:
            # Always emit completion so the controller releases its in-flight
            # task slot and its normal timer can retry the scan later.
            self.signals.completed.emit({"_scan_error": "_DiagnosticsScanTask"})
            return
        self.signals.completed.emit(snapshot)


class _CleanupScanTask(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = _HardwareScanSignals()

    @Slot()
    def run(self) -> None:
        try:
            snapshot = collect_cleanup_preview()
        except Exception:
            # Always emit completion so the controller releases its in-flight
            # task slot and its normal timer can retry the scan later.
            self.signals.completed.emit({"_scan_error": "_CleanupScanTask"})
            return
        self.signals.completed.emit(snapshot)


class ControlCenterController(QObject):
    settingsChanged = Signal()
    systemUpdatesChanged = Signal()
    hardwareChanged = Signal()
    networkChanged = Signal()
    diagnosticsChanged = Signal()
    cleanupChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self._shared_settings_snapshot = self._read_shared_settings_snapshot()
        self._settings_sync_timer = QTimer(self)
        self._settings_sync_timer.setInterval(1500)
        self._settings_sync_timer.timeout.connect(self.refreshSharedSettings)
        self._settings_sync_timer.start()
        self.desktopLayout = DesktopLayoutStore()
        self.plasmaBackups = PlasmaBackupManager()
        self.kdeColorSchemes = KdeColorSchemeManager()
        self.plasmaStyle = PlasmaStyleManager()
        self.monitor = SystemMonitor(self)
        self._hardware_snapshot = {
            key: "Analyse en cours…"
            for key in (
                "cpu", "cpuThreads", "cpuCores", "memory", "memoryTotal", "architecture",
                "firmware", "gamingBaseline", "storage", "gpu", "displayCount", "displays", "vulkan",
                "operatingSystem", "kernel", "bluetooth", "bluetoothDevices",
                "audioServer", "audioOutput", "audioInputs", "controllers",
                "battery", "usbDevices", "network",
            )
        }
        self._hardware_task = None
        self._hardware_timer = QTimer(self)
        self._hardware_timer.setInterval(10_000)
        self._hardware_timer.timeout.connect(self.refreshHardware)
        self._hardware_timer.start()
        QTimer.singleShot(0, self.scanHardwareNow)
        self._network_snapshot = {
            "status": "Analyse en cours…", "defaultInterface": "—",
            "gateway": "—", "dns": "—", "wifiSsid": "—",
            "wifiSignal": "—", "interfaces": [], "counters": {},
        }
        self._network_previous_counters: dict[str, tuple[int, int]] = {}
        self._network_last_scan = 0.0
        self._network_task = None
        self._network_timer = QTimer(self)
        self._network_timer.setInterval(3000)
        self._network_timer.timeout.connect(self.scanNetwork)
        self._network_timer.start()
        QTimer.singleShot(1000, self.scanNetwork)
        self._diagnostics_snapshot = {
            "severity": "Analyse en cours…",
            "summary": "Lecture des indicateurs système…",
            "findings": [],
            "storage": "Analyse en cours…",
            "memory": "Analyse en cours…",
            "temperature": "Analyse en cours…",
            "failedServices": "Analyse en cours…",
            "failedServiceNames": [],
            "recentErrors": "Analyse en cours…",
            "uptime": "Analyse en cours…",
            "loadAverage": "Analyse en cours…",
            "topProcesses": [],
        }
        self._diagnostics_task = None
        self._diagnostics_timer = QTimer(self)
        self._diagnostics_timer.setInterval(30_000)
        self._diagnostics_timer.timeout.connect(self.scanDiagnostics)
        self._diagnostics_timer.start()
        QTimer.singleShot(500, self.scanDiagnostics)
        self._cleanup_snapshot = {
            "thumbnails": {"available": False, "files": 0, "bytes": 0, "size": "Analyse en cours…", "path": ""},
            "trash": {"available": False, "files": 0, "bytes": 0, "size": "Analyse en cours…", "path": ""},
            "totalBytes": 0,
            "totalSize": "Analyse en cours…",
            "note": "Analyse en lecture seule…",
        }
        self._cleanup_task = None
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.setInterval(60_000)
        self._cleanup_timer.timeout.connect(self.scanCleanupPreview)
        self._cleanup_timer.start()
        QTimer.singleShot(750, self.scanCleanupPreview)
        self._system_update_status = "Aucune vérification lancée."
        self._system_update_check_running = False
        self._system_update_timed_out = False
        self._system_update_process = QProcess(self)
        self._system_update_process.finished.connect(self._on_system_update_check_finished)
        self._system_update_process.errorOccurred.connect(self._on_system_update_check_error)
        self._system_update_timeout = QTimer(self)
        self._system_update_timeout.setSingleShot(True)
        self._system_update_timeout.setInterval(SYSTEM_UPDATE_CHECK_TIMEOUT_MS)
        self._system_update_timeout.timeout.connect(self._on_system_update_check_timeout)
        self._deployment_process = QProcess(self)
        self._deployment_process.finished.connect(self._on_deployment_status_finished)
        self._deployment_process.errorOccurred.connect(self._on_deployment_status_error)
        self._deployment_check_running = False
        self._deployment_timed_out = False
        self._deployment_timeout = QTimer(self)
        self._deployment_timeout.setSingleShot(True)
        self._deployment_timeout.setInterval(DEPLOYMENT_STATUS_TIMEOUT_MS)
        self._deployment_timeout.timeout.connect(self._on_deployment_status_timeout)
        self._deployment_timer = QTimer(self)
        self._deployment_timer.setInterval(10 * 60 * 1000)
        self._deployment_timer.timeout.connect(self.refreshPendingSystemUpdate)
        self._deployment_timer.start()
        QTimer.singleShot(2500, self.refreshPendingSystemUpdate)

    def _read_shared_settings_snapshot(self) -> tuple[object, ...]:
        keys = (
            "last_mode", "theme", "performance_profile", "animations_enabled",
            "sounds_enabled", "gaming_overlay_enabled", "notifications_enabled",
            "notification_duration_seconds", "notification_minimum_priority",
            "notification_sounds_enabled", "silent_notifications_in_gaming",
        )
        return self.settings.snapshot(keys)

    @Slot()
    def refreshSharedSettings(self) -> None:
        """Reflect preferences changed by another LEOS process."""
        snapshot = self._read_shared_settings_snapshot()
        if snapshot != self._shared_settings_snapshot:
            self._shared_settings_snapshot = snapshot
            self.settingsChanged.emit()

    @Property("QVariantMap", notify=hardwareChanged)
    def hardwareSnapshot(self) -> dict[str, str]:
        return dict(self._hardware_snapshot)

    @Slot()
    def refreshHardware(self) -> None:
        """Refresh read-only CPU, memory, storage, GPU and peripheral inventory."""
        self.scanHardwareNow()

    @Slot()
    def scanHardwareNow(self) -> None:
        """Run hardware probes off the UI thread and coalesce overlapping scans."""
        if self._hardware_task is not None:
            return
        task = _HardwareScanTask()
        task.signals.completed.connect(self._on_hardware_scan_completed)
        self._hardware_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(dict)
    def _on_hardware_scan_completed(self, snapshot: dict) -> None:
        self._hardware_task = None
        if snapshot.get("_scan_error"):
            return
        if snapshot != self._hardware_snapshot:
            self._hardware_snapshot = snapshot
            self.hardwareChanged.emit()

    @Property("QVariantMap", notify=networkChanged)
    def networkSnapshot(self) -> dict:
        snapshot = dict(self._network_snapshot)
        snapshot.pop("counters", None)
        return snapshot

    @Slot()
    def scanNetwork(self) -> None:
        """Sample network counters off the UI thread without generating traffic."""
        if self._network_task is not None:
            return
        import time
        now = time.monotonic()
        elapsed = now - self._network_last_scan if self._network_last_scan else 0.0
        self._network_last_scan = now
        task = _NetworkScanTask(dict(self._network_previous_counters), elapsed)
        task.signals.completed.connect(self._on_network_scan_completed)
        self._network_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(dict)
    def _on_network_scan_completed(self, snapshot: dict) -> None:
        self._network_task = None
        if snapshot.get("_scan_error"):
            return
        counters = snapshot.get("counters", {})
        if isinstance(counters, dict):
            self._network_previous_counters = {
                str(name): (int(values[0]), int(values[1]))
                for name, values in counters.items()
                if isinstance(values, (tuple, list)) and len(values) == 2
            }
        if snapshot != self._network_snapshot:
            self._network_snapshot = snapshot
            self.networkChanged.emit()

    @Property("QVariantMap", notify=cleanupChanged)
    def cleanupPreview(self) -> dict:
        return dict(self._cleanup_snapshot)

    @Slot()
    def scanCleanupPreview(self) -> None:
        """Preview eligible cache and trash contents without modifying files."""
        if self._cleanup_task is not None:
            return
        task = _CleanupScanTask()
        task.signals.completed.connect(self._on_cleanup_preview_completed)
        self._cleanup_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(dict)
    def _on_cleanup_preview_completed(self, snapshot: dict) -> None:
        self._cleanup_task = None
        if snapshot.get("_scan_error"):
            return
        if snapshot != self._cleanup_snapshot:
            self._cleanup_snapshot = snapshot
            self.cleanupChanged.emit()

    @Property("QVariantMap", notify=diagnosticsChanged)
    def diagnosticsSnapshot(self) -> dict:
        return dict(self._diagnostics_snapshot)

    @Slot()
    def scanDiagnostics(self) -> None:
        """Collect system health indicators without blocking the QML thread."""
        if self._diagnostics_task is not None:
            return
        task = _DiagnosticsScanTask()
        task.signals.completed.connect(self._on_diagnostics_completed)
        self._diagnostics_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(dict)
    def _on_diagnostics_completed(self, snapshot: dict) -> None:
        self._diagnostics_task = None
        if snapshot.get("_scan_error"):
            return
        if snapshot != self._diagnostics_snapshot:
            self._diagnostics_snapshot = snapshot
            self.diagnosticsChanged.emit()

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
    def refreshPendingSystemUpdate(self) -> None:
        """Observe Bazzite's staged deployment without starting an update."""
        if self._deployment_check_running:
            return
        command = rpm_ostree_status_command()
        if not command:
            return
        self._deployment_process.setProgram(command[0])
        self._deployment_process.setArguments(command[1:])
        self._deployment_check_running = True
        self._deployment_timed_out = False
        self._deployment_timeout.start()
        self._deployment_process.start()

    def _on_deployment_status_timeout(self) -> None:
        if not self._deployment_check_running:
            return
        self._deployment_timed_out = True
        self._deployment_process.kill()

    def _on_deployment_status_finished(self, exit_code: int, _exit_status) -> None:
        self._deployment_timeout.stop()
        self._deployment_check_running = False
        if self._deployment_timed_out:
            self._deployment_timed_out = False
            return
        if _exit_status != QProcess.ExitStatus.NormalExit or exit_code != 0:
            return
        payload = bytes(self._deployment_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        pending = pending_deployment_from_status(payload)
        previous = str(self.settings.get("last_notified_system_update", ""))
        if pending is None:
            if previous:
                self.settings.set("last_notified_system_update", "")
            return
        checksum = pending["checksum"]
        message = (
            f"La version {pending['version']} est préparée par le mécanisme de mise à jour Bazzite. "
            "Redémarre lorsque tu le souhaites pour l'appliquer."
        )
        self._set_system_update_status(message)
        if checksum != previous:
            self.settings.set("last_notified_system_update", checksum)
            post_notification("Mise à jour système prête", message, "success")

    def _on_deployment_status_error(self, _error) -> None:
        if self._deployment_timed_out:
            return
        self._deployment_timeout.stop()
        self._deployment_check_running = False

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
        self._system_update_timed_out = False
        self._set_system_update_status("Vérification en cours… Une autorisation système peut être demandée.")
        self._system_update_timeout.start()
        self._system_update_process.start()

    def _on_system_update_check_timeout(self) -> None:
        if not self._system_update_check_running:
            return
        self._system_update_timed_out = True
        self._system_update_process.kill()

    def _on_system_update_check_finished(self, exit_code: int, _exit_status) -> None:
        self._system_update_timeout.stop()
        self._system_update_check_running = False
        if self._system_update_timed_out:
            self._system_update_timed_out = False
            message = "La vérification des mises à jour a dépassé deux minutes. Réessaie lorsque la connexion sera disponible."
            self._set_system_update_status(message)
            post_notification("Vérification trop longue", message, "warning")
            return
        result = (
            interpret_update_check_exit_code(exit_code)
            if _exit_status == QProcess.ExitStatus.NormalExit
            else "error"
        )
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
        if self._system_update_timed_out:
            return
        self._system_update_timeout.stop()
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
    def notificationsEnabled(self) -> bool:
        return bool(self.settings.get("notifications_enabled", True))

    @Property(int, notify=settingsChanged)
    def notificationDuration(self) -> int:
        return int(self.settings.get("notification_duration_seconds", 5))

    @Property(str, notify=settingsChanged)
    def notificationMinimumPriority(self) -> str:
        return str(self.settings.get("notification_minimum_priority", "all"))

    @Property(bool, notify=settingsChanged)
    def notificationSoundsEnabled(self) -> bool:
        return bool(self.settings.get("notification_sounds_enabled", True))

    @Property(bool, notify=settingsChanged)
    def silentNotificationsInGaming(self) -> bool:
        return bool(self.settings.get("silent_notifications_in_gaming", True))

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
    def setNotificationsEnabled(self, enabled: bool) -> None:
        self.settings.set("notifications_enabled", enabled)
        self.settingsChanged.emit()

    @Slot(int)
    def setNotificationDuration(self, seconds: int) -> None:
        if seconds in {3, 5, 8}:
            self.settings.set("notification_duration_seconds", seconds)
            self.settingsChanged.emit()

    @Slot(str)
    def setNotificationMinimumPriority(self, priority: str) -> None:
        if priority in {"all", "important", "critical"}:
            self.settings.set("notification_minimum_priority", priority)
            self.settingsChanged.emit()

    @Slot(bool)
    def setNotificationSoundsEnabled(self, enabled: bool) -> None:
        self.settings.set("notification_sounds_enabled", enabled)
        self.settingsChanged.emit()

    @Slot(bool)
    def setSilentNotificationsInGaming(self, enabled: bool) -> None:
        self.settings.set("silent_notifications_in_gaming", enabled)
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
    def openSystemMonitor(self) -> bool:
        """Open the native KDE process monitor without elevating privileges."""
        return self._start_detached(system_monitor_command())

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
