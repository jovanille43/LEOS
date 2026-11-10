"""Best-effort system metrics for the Gaming dashboard.

Only metrics exposed by the host are reported. FPS and GPU telemetry require
separate game/driver providers and are intentionally not fabricated here.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, QTimer, Signal

try:
    import psutil
except ImportError:  # pragma: no cover - depends on runtime packaging
    psutil = None


class SystemMonitor(QObject):
    metricsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cpu = -1.0
        self._memory = -1.0
        self._cpu_temp = -1.0
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self.refresh)
        if psutil is not None:
            psutil.cpu_percent(interval=None)

    def start(self) -> None:
        self.refresh()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _read_cpu_temperature(self) -> float:
        if psutil is None or not hasattr(psutil, "sensors_temperatures"):
            return -1.0
        try:
            sensors = psutil.sensors_temperatures(fahrenheit=False)
        except (OSError, RuntimeError, NotImplementedError):
            return -1.0
        for entries in sensors.values():
            for entry in entries:
                current = getattr(entry, "current", None)
                if current is not None and current > 0:
                    return float(current)
        return -1.0

    def refresh(self) -> None:
        if psutil is None:
            return
        try:
            self._cpu = float(psutil.cpu_percent(interval=None))
            self._memory = float(psutil.virtual_memory().percent)
            self._cpu_temp = self._read_cpu_temperature()
        except (OSError, RuntimeError):
            return
        self.metricsChanged.emit()

    @Property(float, notify=metricsChanged)
    def cpuUsage(self) -> float:
        return self._cpu

    @Property(float, notify=metricsChanged)
    def memoryUsage(self) -> float:
        return self._memory

    @Property(float, notify=metricsChanged)
    def cpuTemperature(self) -> float:
        return self._cpu_temp

    @Property(bool, constant=True)
    def available(self) -> bool:
        return psutil is not None
