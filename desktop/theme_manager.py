"""Shared live theme palette bridge for every LEOS Qt/QML application."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from desktop.themes import theme_options, visual_tokens_for_theme
from leos_core.settings import SettingsStore


class ThemeManager(QObject):
    """Expose one persisted two-accent theme to QML and refresh across processes."""

    changed = Signal()

    def __init__(self, refresh_interval_ms: int = 1500) -> None:
        super().__init__()
        self.settings = SettingsStore()
        self._theme_id = str(self.settings.get("theme", "leos-original"))
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

    @Slot()
    def refresh(self) -> None:
        """Observe theme changes made by the mode selector or Control Center."""
        selected = str(self.settings.get("theme", "leos-original"))
        if selected != self._theme_id:
            self._theme_id = selected
            self.changed.emit()

    @Slot(str, result=bool)
    def setTheme(self, theme: str) -> bool:
        """Persist a known catalog entry and notify this process immediately."""
        if theme not in {option["id"] for option in theme_options()}:
            return False
        try:
            self.settings.set("theme", theme)
        except (OSError, ValueError, TypeError, KeyError):
            return False
        if theme != self._theme_id:
            self._theme_id = theme
            self.changed.emit()
        return True

    @Slot()
    def shutdown(self) -> None:
        self._timer.stop()
