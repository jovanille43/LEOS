"""Live bridge exposing shared LEOS colors and recolored identity assets."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QTimer, Signal, Slot

from desktop.branding_assets import (
    build_themed_branding_assets,
    cached_themed_branding_asset_urls,
    only_recolored_asset_urls,
    source_asset_urls,
)
from desktop.themes import (
    APPEARANCE_MODES, DEFAULT_COLOR_A, DEFAULT_COLOR_B,
    normalize_color, palette_for_colors, resolve_appearance_mode,
)
from leos_core.settings import SettingsStore


class _BrandingAssetSignals(QObject):
    completed = Signal(object)


class _BrandingAssetTask(QRunnable):
    """Generate derived logos, wallpapers and video intros away from the UI thread."""

    def __init__(self, snapshot: tuple[str, str], generate_videos: bool = True) -> None:
        super().__init__()
        self.snapshot = snapshot
        self.generate_videos = generate_videos
        self.signals = _BrandingAssetSignals()

    @Slot()
    def run(self) -> None:
        try:
            assets = build_themed_branding_assets(
                *self.snapshot, generate_videos=self.generate_videos
            )
        except Exception:
            # A missing optional codec or unreadable source must never prevent
            # the desktop or Gaming interface from starting.
            assets = source_asset_urls()
        self.signals.completed.emit((self.snapshot, assets))


class ThemeController(QObject):
    """Expose live A/B colors, appearance modes and theme-aware identity assets."""

    themeChanged = Signal()
    themeAssetsChanged = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        settings: SettingsStore | None = None,
        *,
        generate_videos: bool = True,
    ) -> None:
        super().__init__(parent)
        self.settings = settings or SettingsStore()
        self.generate_videos = bool(generate_videos)
        self._snapshot = self._read_snapshot()
        self._colors_configured = bool(self.settings.get("theme_colors_configured", False))
        self._appearance_mode = self._read_appearance_mode()
        self._effective_appearance = resolve_appearance_mode(self._appearance_mode)
        self._assets = (
            only_recolored_asset_urls(cached_themed_branding_asset_urls(*self._snapshot))
            if self._colors_configured
            else {}
        )
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

    def _read_appearance_mode(self) -> str:
        value = self.settings.snapshot(("appearance_mode",))[0]
        return str(value or "dark")

    @Property("QVariantMap", notify=themeChanged)
    def themePalette(self) -> dict[str, str]:
        # The A/B pair remains atomic; only neutral surfaces follow appearance.
        return palette_for_colors(*self._snapshot, appearance=self._effective_appearance)

    @Property(str, notify=themeChanged)
    def appearanceMode(self) -> str:
        return self._appearance_mode

    @Property(str, notify=themeChanged)
    def effectiveAppearance(self) -> str:
        return self._effective_appearance

    @Slot(str, result=str)
    def setAppearanceMode(self, mode: str) -> str:
        """Persist the user's dark/light/automatic appearance preference."""
        if mode not in APPEARANCE_MODES:
            return "Mode d'apparence invalide."
        try:
            self.settings.set("appearance_mode", mode)
        except (OSError, ValueError, TypeError, KeyError):
            return "Le mode d'apparence n'a pas pu être enregistré."
        self.refresh()
        return "Apparence mise à jour."

    @Property(str, notify=themeChanged)
    def themeColorA(self) -> str:
        return self._snapshot[0]

    @Property(str, notify=themeChanged)
    def themeColorB(self) -> str:
        return self._snapshot[1]

    @Property(bool, notify=themeChanged)
    def themeColorsConfigured(self) -> bool:
        return self._colors_configured

    @Slot(str, str, result=str)
    def setThemeColors(self, color_a: str, color_b: str) -> str:
        """Persist a complete A/B pair and immediately refresh every bound view."""
        try:
            normalized_a = normalize_color(color_a)
            normalized_b = normalize_color(color_b)
            self.settings.set_many({
                "theme_color_a": normalized_a,
                "theme_color_b": normalized_b,
                "theme_colors_configured": True,
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
        # A neutral, unconfigured first-run preview is not the user's palette.
        # Avoid recoloring large images/videos until the user explicitly saves A/B.
        if (
            self._closed
            or not self._colors_configured
            or self._asset_task is not None
            or self._asset_attempt_snapshot == self._snapshot
        ):
            return
        self._asset_attempt_snapshot = self._snapshot
        task = _BrandingAssetTask(self._snapshot, self.generate_videos)
        task.signals.completed.connect(self._on_assets_generated)
        self._asset_task = task
        QThreadPool.globalInstance().start(task)

    @Slot(object)
    def _on_assets_generated(self, result: object) -> None:
        self._asset_task = None
        if self._closed or not isinstance(result, tuple) or len(result) != 2:
            return
        snapshot, assets = result
        if snapshot == self._snapshot and self._colors_configured and isinstance(assets, dict):
            self._assets = only_recolored_asset_urls(assets)
            self.themeAssetsChanged.emit()
        if snapshot != self._snapshot:
            self._start_asset_generation()

    @Slot()
    def refresh(self) -> None:
        """Reflect shared settings and time-based light/dark transitions across LEOS apps."""
        snapshot = self._read_snapshot()
        colors_configured = bool(self.settings.get("theme_colors_configured", False))
        appearance_mode = self._read_appearance_mode()
        effective_appearance = resolve_appearance_mode(appearance_mode)
        appearance_changed = (
            appearance_mode != self._appearance_mode
            or effective_appearance != self._effective_appearance
        )
        configured_changed = colors_configured != self._colors_configured
        if appearance_changed:
            self._appearance_mode = appearance_mode
            self._effective_appearance = effective_appearance
        if configured_changed:
            self._colors_configured = colors_configured
            if self._colors_configured:
                # Also retry when the user intentionally chooses the neutral
                # default pair, which does not change the color snapshot.
                self._asset_attempt_snapshot = None
            elif self._assets:
                self._assets = {}
                self.themeAssetsChanged.emit()

        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self._asset_attempt_snapshot = None
            self.themeChanged.emit()
            self._start_asset_generation()
        elif appearance_changed or configured_changed:
            self.themeChanged.emit()
            if configured_changed and self._colors_configured:
                # The user may explicitly keep the neutral default pair, so the
                # configured flag must be enough to start asset generation.
                self._start_asset_generation()

        # Another LEOS process may own the generation lock. Adopt its derived
        # files on a later poll without repeatedly competing for that lock.
        cached = (
            only_recolored_asset_urls(cached_themed_branding_asset_urls(*self._snapshot))
            if self._colors_configured
            else {}
        )
        if cached != self._assets:
            self._assets = cached
            self.themeAssetsChanged.emit()

    def shutdown(self) -> None:
        self._closed = True
        self._timer.stop()
