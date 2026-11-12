"""Read-only GPU telemetry from Linux DRM sysfs."""

import csv
import re
import shutil
import subprocess
from pathlib import Path


def _nvidia_smi_metrics() -> dict[str, object] | None:
    """Read NVIDIA proprietary-driver telemetry when nvidia-smi is available."""
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    for row in csv.reader(result.stdout.splitlines()):
        if len(row) != 5:
            continue
        name = row[0].strip()
        if not name:
            continue
        try:
            usage = float(row[1].strip())
            temperature = float(row[2].strip())
            memory_used_mb = float(row[3].strip())
            memory_total_mb = float(row[4].strip())
        except ValueError:
            continue
        if not 0 <= usage <= 100:
            usage = -1.0
        if not 0 < temperature < 150:
            temperature = -1.0
        if memory_used_mb < 0:
            memory_used = -1
        else:
            memory_used = int(memory_used_mb * 1024 * 1024)
        if memory_total_mb <= 0:
            memory_total = -1
        else:
            memory_total = int(memory_total_mb * 1024 * 1024)
        return {
            "name": name,
            "usage": usage,
            "temperature": temperature,
            "memory_used": memory_used,
            "memory_total": memory_total,
        }
    return None


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
        selected = max(candidates, key=lambda item: item[0])[1]
        # NVIDIA's proprietary driver does not consistently expose utilization
        # through DRM sysfs; use its supported CLI only when the matching
        # telemetry fields are missing.
        if str(selected["name"]).startswith("NVIDIA"):
            nvidia = _nvidia_smi_metrics()
            if nvidia is not None:
                for key in ("usage", "temperature", "memory_used", "memory_total"):
                    unavailable = -1 if key.startswith("memory_") else -1.0
                    if selected[key] == unavailable and nvidia[key] != unavailable:
                        selected[key] = nvidia[key]
                if selected["name"] == "NVIDIA · PCI " or "PCI" in str(selected["name"]):
                    selected["name"] = str(nvidia["name"])
        return selected
    nvidia = _nvidia_smi_metrics()
    if nvidia is not None:
        return nvidia
    return {
        "name": "GPU non détecté",
        "usage": -1.0,
        "temperature": -1.0,
        "memory_used": -1,
        "memory_total": -1,
    }
