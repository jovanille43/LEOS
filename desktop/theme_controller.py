"""Live bridge exposing shared LEOS colors and recolored identity assets."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from desktop.branding_assets import (
    build_themed_branding_assets,
    cached_themed_branding_asset_urls,
    source_asset_urls,
)
from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, normalize_color, palette_for_colors
from leos_core.settings import SettingsStore


class _BrandingAssetSignals(QObject):
    completed = Signal(object)


class _BrandingAssetTask(QRunnable):
    """Generate derived logos, wallpapers and video intros away from the UI thread."""

    def __init__(self, snapshot: tuple[str, str]) -> None:
        super().__init__()
        self.snapshot = snapshot
        self.signals = _BrandingAssetSignals()

    @Slot()
    def run(self) -> None:
        try:
            assets = build_themed_branding_assets(*self.snapshot)
        except Exception:
            # A missing optional codec or unreadable source must never prevent
            # the desktop or Gaming interface from starting.
            assets = source_asset_urls()
        self.signals.completed.emit((self.snapshot, assets))


class ThemeController(QObject):
    """Expose and refresh the shared A/B gradient and theme-aware identity assets."""

    themeChanged = Signal()
    themeAssetsChanged = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        settings: SettingsStore | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings or SettingsStore()
        self._snapshot = self._read_snapshot()
        self._assets = cached_themed_branding_asset_urls(*self._snapshot)
        self._asset_task: _BrandingAssetTask | None = None
        self._asset_attempt_snapshot: tuple[str, str] | None = None
        self._closed = False
        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self._start_asset_generation()

    def _read_snapshot(self) -> tuple[str, str]:
        values = self.settings.snapshot(("theme_color_a", "theme_color_b"))
        return (
            str(values[0] or DEFAULT_COLOR_A),
            str(values[1] or DEFAULT_COLOR_B),
        )

    @Property("QVariantMap", notify=themeChanged)
    def themePalette(self) -> dict[str, str]:
        return palette_for_colors(
            str(self.settings.get("theme_color_a", DEFAULT_COLOR_A)),
            str(self.settings.get("theme_color_b", DEFAULT_COLOR_B)),
        )

    @Property(str, notify=themeChanged)
    def themeColorA(self) -> str:
        return str(self.settings.get("theme_color_a", DEFAULT_COLOR_A))

    @Property(str, notify=themeChanged)
    def themeColorB(self) -> str:
        return str(self.settings.get("theme_color_b", DEFAULT_COLOR_B))

    @Slot(str, str, result=str)
    def setThemeColors(self, color_a: str, color_b: str) -> str:
        """Persist a complete A/B pair and immediately refresh every bound view."""
        try:
            normalized_a = normalize_color(color_a)
            normalized_b = normalize_color(color_b)
            self.settings.set_many({
                "theme_color_a": normalized_a,
                "theme_color_b": normalized_b,
            })
        except (OSError, ValueError, TypeError, KeyError):
            return "Les couleurs n'ont pas pu être enregistrées. Vérifie le format #RRGGBB."
        self.refresh()
        return "Dégradé LEOS mis à jour."

    @Property(str, notify=themeAssetsChanged)
    def desktopLogoUrl(self) -> str:
        return self._assets.get("desktopLogoUrl", "")

    @Property(str, notify=themeAssetsChanged)
    def gamingLogoUrl(self) -> str:
        return self._assets.get("gamingLogoUrl", "")

    @Property(str, notify=themeAssetsChanged)
    def desktopWallpaperUrl(self) -> str:
        return self._assets.get("desktopWallpaperUrl", "")

    @Property(str, notify=themeAssetsChanged)
    def gamingWallpaperUrl(self) -> str:
        return self._assets.get("gamingWallpaperUrl", "")

    @Property(str, notify=themeAssetsChanged)
    def desktopIntroUrl(self) -> str:
        return self._assets.get("desktopIntroUrl", "")

    @Property(str, notify=themeAssetsChanged)
    def gamingIntroUrl(self) -> str:
        return self._assets.get("gamingIntroUrl", "")

    def _start_asset_generation(self) -> None:
        if self._closed or self._asset_task is not None or self._asset_attempt_snapshot == self._snapshot:
            return
        self._asset_attempt_snapshot = self._snapshot
        task = _BrandingAssetTask(self._snapshot)
        task.signals.completed.connect(self._on_assets_generated)
        self._asset_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(object)
    def _on_assets_generated(self, result: object) -> None:
        self._asset_task = None
        if self._closed or not isinstance(result, tuple) or len(result) != 2:
            return
        snapshot, assets = result
        if snapshot == self._snapshot and isinstance(assets, dict):
            self._assets = dict(assets)
            self.themeAssetsChanged.emit()
        if snapshot != self._snapshot:
            self._start_asset_generation()

    @Slot()
    def refresh(self) -> None:
        """Reflect a gradient changed by Control Center or another LEOS process."""
        snapshot = self._read_snapshot()
        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self._asset_attempt_snapshot = None
            self.themeChanged.emit()
            self._start_asset_generation()

        # Another LEOS process may own the generation lock. Adopt its derived
        # files on a later poll without repeatedly competing for that lock.
        cached = cached_themed_branding_asset_urls(*self._snapshot)
        if cached != self._assets:
            self._assets = cached
            self.themeAssetsChanged.emit()

    def shutdown(self) -> None:
        self._closed = True
        self._timer.stop()
