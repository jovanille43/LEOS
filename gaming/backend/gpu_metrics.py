"""Read-only GPU telemetry from Linux DRM sysfs."""

from pathlib import Path


def read_gpu_metrics(sys_root: Path = Path("/sys")) -> dict[str, object]:
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

