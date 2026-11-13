"""Shared live theme palette and artwork bridge for LEOS Qt/QML applications."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from desktop.theme_assets import ThemeAssetManager
from desktop.themes import theme_options, visual_tokens_for_theme
from leos_core.settings import SettingsStore


class _ThemeAssetSignals(QObject):
    completed = Signal(str, object)
    failed = Signal(str, str)


class _ThemeAssetTask(QRunnable):
    def __init__(self, theme: str) -> None:
        super().__init__()
        self.theme = theme
        self.signals = _ThemeAssetSignals()

    @Slot()
    def run(self) -> None:
        try:
            assets = ThemeAssetManager().paths_for_theme(self.theme)
        except Exception as error:
            self.signals.failed.emit(self.theme, str(error))
            return
        self.signals.completed.emit(self.theme, assets)


class ThemeManager(QObject):
    """Expose one persisted two-accent theme and its derived artwork to QML."""

    changed = Signal()
    assetGenerationFailed = Signal(str)

    def __init__(self, refresh_interval_ms: int = 1500) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self._theme_id = str(self.settings.get("theme", "leos-original"))
        self._asset_manager = ThemeAssetManager()
        self._asset_tasks: list[_ThemeAssetTask] = []
        self._asset_paths = self._asset_manager.paths_for_theme(self._theme_id)
        self._timer = QTimer(self)
        self._timer.setInterval(max(250, int(refresh_interval_ms)))
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    @Property(str, notify=changed)
    def currentTheme(self) -> str:
        return self._theme_id

    @Property("QVariantMap", notify=changed)
    def palette(self) -> dict[str, str]:
        return visual_tokens_for_theme(self._theme_id)

    @Property("QVariantList", notify=changed)
    def options(self) -> list[dict[str, str]]:
        return theme_options()

    @Property("QVariantMap", notify=changed)
    def assets(self) -> dict[str, str]:
        return dict(self._asset_paths)

    def _generate_assets(self, theme: str) -> None:
        task = _ThemeAssetTask(theme)
        task.signals.completed.connect(self._on_assets_completed)
        task.signals.failed.connect(self._on_assets_failed)
        self._asset_tasks.append(task)
        QThreadPool.globalInstance().start(task)

    @Slot(str, object)
    def _on_assets_completed(self, theme: str, assets: object) -> None:
        self._asset_tasks = [task for task in self._asset_tasks if task.theme != theme]
        if theme != self._theme_id or not isinstance(assets, dict):
            return
        self._asset_paths = dict(assets)
        self.changed.emit()

    @Slot(str, str)
    def _on_assets_failed(self, theme: str, message: str) -> None:
        self._asset_tasks = [task for task in self._asset_tasks if task.theme != theme]
        if theme == self._theme_id:
            self.assetGenerationFailed.emit(
                "Les logos et fonds LEOS d'origine restent utilisés : "
                "la variante graphique n'a pas pu être générée."
            )

    @Slot()
    def refresh(self) -> None:
        """Observe theme changes made by the mode selector or Control Center."""
        selected = str(self.settings.get("theme", "leos-original"))
        if selected == self._theme_id:
            return
        self._theme_id = selected
        self.changed.emit()
        self._generate_assets(selected)

    @Slot(str, result=bool)
    def setTheme(self, theme: str) -> bool:
        """Persist a known catalog entry; the other LEOS processes refresh shortly."""
        if theme not in {option["id"] for option in theme_options()}:
            return False
        try:
            self.settings.set("theme", theme)
        except (OSError, ValueError, TypeError, KeyError):
            return False
        self.refresh()
        return True

    @Slot()
    def shutdown(self) -> None:
        self._timer.stop()
