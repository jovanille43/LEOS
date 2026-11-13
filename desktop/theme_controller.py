"""Live bridge exposing the shared LEOS A/B gradient to small desktop apps."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, palette_for_colors
from leos_core.settings import SettingsStore


class ThemeController(QObject):
    """Expose and refresh the user-selected gradient from shared LEOS settings."""

    themeChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.settings = SettingsStore()
        self._snapshot = self._read_snapshot()
        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def _read_snapshot(self) -> tuple[object, ...]:
        return self.settings.snapshot(("theme_color_a", "theme_color_b"))

    @Property("QVariantMap", notify=themeChanged)
    def themePalette(self) -> dict[str, str]:
        return palette_for_colors(
            str(self.settings.get("theme_color_a", DEFAULT_COLOR_A)),
            str(self.settings.get("theme_color_b", DEFAULT_COLOR_B)),
        )

    @Slot()
    def refresh(self) -> None:
        """Reflect changes made by Control Center or another LEOS process."""
        snapshot = self._read_snapshot()
        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self.themeChanged.emit()

    def shutdown(self) -> None:
        self._timer.stop()
