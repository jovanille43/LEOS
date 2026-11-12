"""Read-only GPU telemetry from Linux DRM sysfs."""

import re
from pathlib import Path


def read_gpu_metrics(sys_root: Path = Path("/sys")) -> dict[str, object]:
    """Read the best available GPU telemetry without assuming card0 is primary."""
    vendor_names = {"0x1002": "AMD", "0x8086": "Intel", "0x10de": "NVIDIA"}
    try:
        cards = sorted(
            card
            for card in (sys_root / "class" / "drm").glob("card[0-9]*")
            if re.fullmatch(r"card\d+", card.name)
        )
    except OSError:
        cards = []

    candidates: list[tuple[tuple[int, int, int, int], dict[str, object]]] = []
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
        temperature = -1.0
        used = total = -1
        try:
            value = float((device / "gpu_busy_percent").read_text(encoding="ascii").strip())
            if 0 <= value <= 100:
                usage = value
        except (OSError, ValueError, UnicodeError):
            pass

        temperature_candidates: list[tuple[int, float]] = []
        try:
            for sensor in device.glob("hwmon/hwmon*/temp*_input"):
                stem = sensor.name.removesuffix("_input")
                try:
                    label = (
                        (sensor.parent / f"{stem}_label")
                        .read_text(encoding="ascii").strip().casefold()
                    )
                    milli_celsius = int(sensor.read_text(encoding="ascii").strip())
                except (OSError, ValueError, UnicodeError):
                    continue
                celsius = milli_celsius / 1000.0
                if 0 < celsius < 150:
                    priority = (
                        0 if label in {"edge", "gpu", "gt"}
                        else 1 if label == "junction"
                        else 2
                    )
                    if priority < 2:
                        temperature_candidates.append((priority, celsius))
        except OSError:
            pass
        if temperature_candidates:
            temperature = min(temperature_candidates, key=lambda item: item[0])[1]

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

        snapshot = {
            "name": name,
            "usage": usage,
            "temperature": temperature,
            "memory_used": used,
            "memory_total": total,
        }
        # Prefer a GPU that actually exports telemetry. VRAM capacity is a
        # useful discrete-GPU signal on hybrid laptops; unavailable values
        # remain -1 and are never inferred from the GPU model.
        score = (
            int(total > 0),
            int(usage >= 0),
            int(temperature >= 0),
            int(used >= 0),
        )
        candidates.append((score, snapshot))

    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return {
        "name": "GPU non détecté",
        "usage": -1.0,
        "temperature": -1.0,
        "memory_used": -1,
        "memory_total": -1,
    }
