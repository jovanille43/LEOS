"""Best-effort system metrics shared by LEOS Gaming and Control Center.

Only metrics exposed by the host are reported. FPS and GPU telemetry require
separate game/driver providers and are intentionally not fabricated here.
"""

from __future__ import annotations

import time
from pathlib import Path

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
        self._disk_usage = -1.0
        self._network_receive_rate = -1.0
        self._network_send_rate = -1.0
        self._gpu_name = "GPU non détecté"
        self._gpu_usage = -1.0
        self._gpu_memory_used = -1
        self._gpu_memory_total = -1
        self._last_network_sample: tuple[float, int, int] | None = None
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
        cpu_sensor_hints = ("coretemp", "k10temp", "zenpower", "cpu", "package id", "tctl", "tdie")
        for chip_name, entries in sensors.items():
            labels = " ".join(
                [chip_name] + [str(getattr(entry, "label", "")) for entry in entries]
            ).casefold()
            if not any(hint in labels for hint in cpu_sensor_hints):
                continue
            for entry in entries:
                current = getattr(entry, "current", None)
                if current is not None and current > 0:
                    return float(current)
        return -1.0

    def _read_disk_usage(self) -> float:
        if psutil is None:
            return -1.0
        try:
            return float(psutil.disk_usage("/").percent)
        except (OSError, RuntimeError):
            return -1.0

    def _read_network_rates(self) -> tuple[float, float]:
        if psutil is None:
            return -1.0, -1.0
        try:
            counters = psutil.net_io_counters()
        except (OSError, RuntimeError):
            return -1.0, -1.0
        if counters is None:
            return -1.0, -1.0

        now = time.monotonic()
        current = (now, int(counters.bytes_recv), int(counters.bytes_sent))
        previous = self._last_network_sample
        self._last_network_sample = current
        if previous is None:
            return -1.0, -1.0

        elapsed = now - previous[0]
        if elapsed <= 0:
            return -1.0, -1.0
        received = max(0, current[1] - previous[1]) / elapsed
        sent = max(0, current[2] - previous[2]) / elapsed
        return float(received), float(sent)


    @staticmethod
    def _read_gpu_metrics(sys_root: Path = Path("/sys")) -> dict[str, object]:
        """Read conservative GPU telemetry from Linux DRM sysfs (read-only)."""
        vendor_names = {"0x1002": "AMD", "0x8086": "Intel", "0x10de": "NVIDIA"}
        try:
            cards = sorted((sys_root / "class" / "drm").glob("card[0-9]*"))
        except OSError:
            cards = []
        for card in cards:
            device = card / "device"
            try:
                if not device.exists():
                    continue
                vendor_id = (device / "vendor").read_text(encoding="ascii").strip().lower()
                device_id = (device / "device").read_text(encoding="ascii").strip().lower()
            except (OSError, UnicodeError):
                continue
            vendor = vendor_names.get(vendor_id, "GPU")
            name = f"{vendor} · PCI {device_id}" if device_id else vendor
            usage = -1.0
            used = total = -1
            try:
                value = float((device / "gpu_busy_percent").read_text(encoding="ascii").strip())
                if 0 <= value <= 100:
                    usage = value
            except (OSError, ValueError, UnicodeError):
                pass
            try:
                value = int((device / "mem_info_vram_used").read_text(encoding="ascii").strip())
                if value >= 0:
                    used = value
            except (OSError, ValueError, UnicodeError):
                pass
            try:
                value = int((device / "mem_info_vram_total").read_text(encoding="ascii").strip())
                if value > 0:
                    total = value
            except (OSError, ValueError, UnicodeError):
                pass
            return {"name": name, "usage": usage, "memory_used": used, "memory_total": total}
        return {"name": "GPU non détecté", "usage": -1.0, "memory_used": -1, "memory_total": -1}

    def refresh(self) -> None:
        if psutil is None:
            return
        try:
            self._cpu = float(psutil.cpu_percent(interval=None))
            self._memory = float(psutil.virtual_memory().percent)
            self._cpu_temp = self._read_cpu_temperature()
            self._disk_usage = self._read_disk_usage()
            self._network_receive_rate, self._network_send_rate = self._read_network_rates()
            gpu = self._read_gpu_metrics()
            self._gpu_name = str(gpu["name"])
            self._gpu_usage = float(gpu["usage"])
            self._gpu_memory_used = int(gpu["memory_used"])
            self._gpu_memory_total = int(gpu["memory_total"])
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

    @Property(float, notify=metricsChanged)
    def diskUsage(self) -> float:
        return self._disk_usage

    @Property(float, notify=metricsChanged)
    def networkReceiveRate(self) -> float:
        return self._network_receive_rate

    @Property(float, notify=metricsChanged)
    def networkSendRate(self) -> float:
        return self._network_send_rate


    @Property(str, notify=metricsChanged)
    def gpuName(self) -> str:
        return self._gpu_name

    @Property(float, notify=metricsChanged)
    def gpuUsage(self) -> float:
        return self._gpu_usage

    @Property(int, notify=metricsChanged)
    def gpuMemoryUsed(self) -> int:
        return self._gpu_memory_used

    @Property(int, notify=metricsChanged)
    def gpuMemoryTotal(self) -> int:
        return self._gpu_memory_total

    @Property(bool, constant=True)
    def available(self) -> bool:
        return psutil is not None
