"""Shared live theme palette and artwork bridge for LEOS Qt/QML applications."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from desktop.theme_assets import ThemeAssetManager
from desktop.themes import theme_options, visual_tokens_for_theme
from leos_core.settings import SettingsStore


class _ThemeAssetSignals(QObject):
    completed = Signal(str, object)
    failed = Signal(str, str)


class _ThemeAssetTask(QRunnable):
    """Generate light-weight logo and wallpaper resources away from the UI thread."""

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
    """Expose the persisted palette and safely managed derivative artwork to QML."""

    changed = Signal()
    assetGenerationFailed = Signal(str)

    def __init__(self, refresh_interval_ms: int = 1500) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self._theme_id = str(self.settings.get("theme", "leos-original"))
        self._asset_manager = ThemeAssetManager()
        self._asset_tasks: list[_ThemeAssetTask] = []
        self._asset_paths = self._original_assets()
        self._video_worker_theme = ""
        if self._theme_id != "leos-original":
            self._generate_assets(self._theme_id)
            self._start_video_worker(self._theme_id)
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

    def _original_assets(self) -> dict[str, str]:
        branding = self._asset_manager.branding_dir
        return {
            "desktop_logo": (branding / "desktop-logo-alpha.png").resolve().as_uri(),
            "gaming_logo": (branding / "gaming-logo-alpha.png").resolve().as_uri(),
            "desktop_wallpaper": (branding / "wallpapers" / "desktop-leos.svg").resolve().as_uri(),
            "gaming_wallpaper": (branding / "wallpapers" / "gaming-leos.svg").resolve().as_uri(),
            "desktop_intro": (branding / "animations" / "desktop-intro.mov").resolve().as_uri(),
            "gaming_intro": (branding / "animations" / "gaming-intro.mp4").resolve().as_uri(),
            "videos_recolored": "true",
        }

    def _generate_assets(self, theme: str) -> None:
        task = _ThemeAssetTask(theme)
        task.signals.completed.connect(self._on_assets_completed)
        task.signals.failed.connect(self._on_assets_failed)
        self._asset_tasks.append(task)
        QThreadPool.globalInstance().start(task)

    def _start_video_worker(self, theme: str) -> None:
        """Start a detached, serialized worker so closing the selector cannot cancel encoding."""
        palette = visual_tokens_for_theme(theme)
        if (
            palette["accent_primary"].lower() == "#00d9ff"
            and palette["accent_secondary"].lower() == "#e33bff"
        ):
            self._asset_paths.update(self._original_assets())
            return

        cached = self._asset_manager.cached_video_paths_for_theme(theme)
        if cached is not None:
            self._asset_paths.update(cached)
            self.changed.emit()
            return

        if self._video_worker_theme == theme:
            return
        self._video_worker_theme = theme
        project_root = Path(__file__).resolve().parents[1]
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "desktop.theme_assets",
                    "--generate-videos",
                    theme,
                ],
                cwd=project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
        except OSError:
            # Keep the official videos active if a background worker cannot start.
            self._video_worker_theme = ""

    @Slot(str, object)
    def _on_assets_completed(self, theme: str, assets: object) -> None:
        self._asset_tasks = [task for task in self._asset_tasks if task.theme != theme]
        if theme != self._theme_id or not isinstance(assets, dict):
            return
        self._asset_paths.update(assets)
        self.changed.emit()

    @Slot(str, str)
    def _on_assets_failed(self, theme: str, _message: str) -> None:
        self._asset_tasks = [task for task in self._asset_tasks if task.theme != theme]
        if theme == self._theme_id:
            self.assetGenerationFailed.emit(
                "Les ressources officielles LEOS restent affichées : "
                "la variante graphique n'a pas pu être préparée."
            )

    @Slot()
    def refresh(self) -> None:
        """Observe changes made by other LEOS processes and completed video jobs."""
        selected = str(self.settings.get("theme", "leos-original"))
        if selected != self._theme_id:
            self._theme_id = selected
            self._asset_paths = self._original_assets()
            self.changed.emit()
            if selected != "leos-original":
                self._generate_assets(selected)
                self._start_video_worker(selected)
            self._video_worker_theme = selected
            return

        if selected != "leos-original":
            cached = self._asset_manager.cached_video_paths_for_theme(selected)
            if cached is not None:
                changes = {
                    key: value
                    for key, value in cached.items()
                    if self._asset_paths.get(key) != value
                }
                if changes:
                    self._asset_paths.update(changes)
                    self._video_worker_theme = ""
                    self.changed.emit()
            elif self._video_worker_theme != selected:
                self._start_video_worker(selected)

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
