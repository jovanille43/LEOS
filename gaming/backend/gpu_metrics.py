"""Read-only GPU telemetry from Linux DRM sysfs."""

import csv
import re
import shutil
import subprocess
from pathlib import Path


_PCI_ADDRESS = re.compile(
    r"^(?:0x)?([0-9a-f]{4,8}):([0-9a-f]{2}):([0-9a-f]{2})\.([0-7])$",
    re.IGNORECASE,
)


def _normalize_pci_address(value: str) -> str | None:
    """Normalize sysfs and nvidia-smi PCI addresses to Linux domain:bus:device.fn."""
    match = _PCI_ADDRESS.fullmatch(value.strip())
    if not match:
        return None
    domain, bus, device, function = match.groups()
    domain_number = int(domain, 16)
    if domain_number > 0xFFFF:
        return None
    return f"{domain_number:04x}:{bus.lower()}:{device.lower()}.{function}"


def _pci_address_for_device(device: Path) -> str | None:
    """Resolve a DRM device symlink to its PCI BDF without assuming card order."""
    try:
        resolved = device.resolve(strict=True)
    except OSError:
        return None
    for parent in (resolved, *resolved.parents):
        address = _normalize_pci_address(parent.name)
        if address:
            return address
    return None


def _parse_nvidia_value(
    value: str, *, minimum: float = 0, maximum: float | None = None
) -> float:
    try:
        parsed = float(value.strip())
    except (TypeError, ValueError):
        return -1.0
    if parsed < minimum or (maximum is not None and parsed > maximum):
        return -1.0
    return parsed


def _nvidia_smi_devices() -> dict[str, dict[str, object]]:
    """Read NVIDIA telemetry keyed by PCI address so hybrid GPUs cannot be mixed."""
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {}
    try:
        result = subprocess.run(
            [
                executable,
                "--query-gpu=pci.bus_id,name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=2.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0:
        return {}

    devices: dict[str, dict[str, object]] = {}
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) != 6:
            continue
        pci_address = _normalize_pci_address(row[0])
        name = row[1].strip()
        if not pci_address or not name:
            continue
        usage = _parse_nvidia_value(row[2], maximum=100)
        temperature = _parse_nvidia_value(row[3], minimum=0, maximum=150)
        memory_used_mb = _parse_nvidia_value(row[4])
        memory_total_mb = _parse_nvidia_value(row[5], minimum=0.000001)
        devices[pci_address] = {
            "name": name,
            "usage": usage,
            "temperature": temperature,
            "memory_used": int(memory_used_mb * 1024 * 1024) if memory_used_mb >= 0 else -1,
            "memory_total": int(memory_total_mb * 1024 * 1024) if memory_total_mb >= 0 else -1,
        }
    return devices


def _nvidia_metrics_score(metrics: dict[str, object]) -> tuple[int, int, int, int]:
    """Rank complete NVIDIA telemetry without guessing from model names."""
    return (
        int(metrics["memory_total"] > 0),
        int(metrics["usage"] >= 0),
        int(metrics["temperature"] >= 0),
        int(metrics["memory_used"] >= 0),
    )


def _best_nvidia_metrics(
    devices: dict[str, dict[str, object]],
) -> dict[str, object] | None:
    """Choose a deterministic fallback only when no DRM GPU can be matched."""
    if not devices:
        return None
    return max(devices.values(), key=_nvidia_metrics_score)


def read_gpu_metrics(sys_root: Path = Path("/sys")) -> dict[str, object]:
    """Read the best available GPU telemetry and match NVIDIA data by PCI identity."""
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
    nvidia_devices: dict[str, dict[str, object]] | None = None
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
        pci_address = _pci_address_for_device(device)
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

        # NVIDIA's proprietary driver may expose richer metrics through its
        # own CLI. Only merge a row whose PCI identity matches this DRM card.
        if vendor_id == "0x10de" and pci_address:
            if nvidia_devices is None:
                nvidia_devices = _nvidia_smi_devices()
            nvidia = nvidia_devices.get(pci_address)
            if nvidia is not None:
                for key in ("usage", "temperature", "memory_used", "memory_total"):
                    unavailable = -1 if key.startswith("memory_") else -1.0
                    if snapshot[key] == unavailable and nvidia[key] != unavailable:
                        snapshot[key] = nvidia[key]
                if name.startswith("NVIDIA · PCI"):
                    snapshot["name"] = str(nvidia["name"])

        # Prefer devices exposing actual VRAM and live metrics; missing values
        # remain unavailable and are never inferred from a GPU model or vendor.
        score = (
            int(snapshot["memory_total"] > 0),
            int(snapshot["usage"] >= 0),
            int(snapshot["temperature"] >= 0),
            int(snapshot["memory_used"] >= 0),
        )
        candidates.append((score, snapshot))

    if candidates:
        return max(candidates, key=lambda item: item[0])[1]

    # A fallback is useful on systems where NVIDIA exposes telemetry but DRM
    # device nodes are temporarily unavailable. Do not merge it into an
    # unrelated GPU when PCI identity cannot be established.
    if nvidia_devices is None:
        nvidia_devices = _nvidia_smi_devices()
    nvidia = _best_nvidia_metrics(nvidia_devices)
    if nvidia is not None:
        return nvidia
    return {
        "name": "GPU non détecté",
        "usage": -1.0,
        "temperature": -1.0,
        "memory_used": -1,
        "memory_total": -1,
    }
