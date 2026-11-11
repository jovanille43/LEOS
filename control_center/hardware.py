"""Read-only hardware and peripheral inventory for the LEOS Control Center."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence


def _run(command: Sequence[str], timeout: float = 1.5) -> str:
    """Run a bounded, read-only system query; missing tools never break the UI."""
    try:
        result = subprocess.run(
            list(command), capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _read(path: str | Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _cpu_details() -> tuple[str, str]:
    data = _read("/proc/cpuinfo")
    model = ""
    for line in data.splitlines():
        if line.lower().startswith(("model name", "hardware")) and ":" in line:
            model = line.split(":", 1)[1].strip()
            if model:
                break
    logical = sum(1 for line in data.splitlines() if line.lower().startswith("processor"))
    if not logical:
        logical = os.cpu_count() or 0
    return model or "Non détecté", f"{logical} thread(s)" if logical else "Indisponible"


def _memory_details() -> str:
    values: dict[str, int] = {}
    for line in _read("/proc/meminfo").splitlines():
        match = re.match(r"^(MemTotal|MemAvailable):\s+(\d+)\s+kB", line)
        if match:
            values[match.group(1)] = int(match.group(2)) * 1024
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", 0)
    if not total:
        return "Indisponible"
    used = max(0, total - available)
    gib = 1024 ** 3
    return f"{used / gib:.1f} / {total / gib:.1f} Gio utilisés"


def _gpu_details() -> str:
    found: list[str] = []
    vendor_names = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}
    try:
        devices = sorted(Path("/sys/class/drm").glob("card[0-9]/device"))
    except OSError:
        devices = []
    for device in devices:
        vendor = _read(device / "vendor").strip().lower()
        if not vendor:
            continue
        name = vendor_names.get(vendor, f"GPU {vendor}")
        driver_link = device / "driver"
        try:
            driver = driver_link.resolve(strict=True).name
        except OSError:
            driver = ""
        label = f"{name} ({driver})" if driver else name
        if label not in found:
            found.append(label)
    if found:
        return " · ".join(found)
    lspci = _run(["lspci", "-nn"], timeout=2.0)
    lines = [line.split(": ", 1)[-1] for line in lspci.splitlines() if "VGA compatible controller" in line or "3D controller" in line or "Display controller" in line]
    return " · ".join(lines) if lines else "Non détecté"


def _bluetooth_details() -> tuple[str, str]:
    service = _run(["systemctl", "show", "-p", "ActiveState", "--value", "bluetooth"])
    if service != "active":
        return ("Inactif" if service else "État indisponible", "Aucun périphérique connecté détecté")
    info = _run(["bluetoothctl", "show"])
    if not info:
        return "Service actif · contrôleur indisponible", "Liste indisponible"
    powered = re.search(r"Powered:\s*(yes|no)", info, re.IGNORECASE)
    status = "Activé" if powered and powered.group(1).lower() == "yes" else "Désactivé"
    devices = _run(["bluetoothctl", "devices", "Connected"])
    names = []
    for line in devices.splitlines():
        match = re.match(r"Device\s+[0-9A-F:]+\s+(.+)", line.strip(), re.IGNORECASE)
        if match:
            names.append(match.group(1))
    return status, " · ".join(names) if names else "Aucun périphérique connecté"


def _audio_details() -> tuple[str, str, str]:
    info = _run(["pactl", "info"])
    sinks = _run(["pactl", "list", "short", "sinks"])
    sources = _run(["pactl", "list", "short", "sources"])
    server = "PipeWire / PulseAudio" if info else "Serveur audio indisponible"
    default_sink = ""
    match = re.search(r"^Default Sink:\s*(.+)$", info, re.MULTILINE)
    if match:
        default_sink = match.group(1).strip()
    output_names = []
    for line in sinks.splitlines():
        columns = line.split()
        if len(columns) >= 2:
            output_names.append(columns[1])
    input_count = sum(1 for line in sources.splitlines() if line.split() and not line.split()[1].endswith(".monitor"))
    output = default_sink or (output_names[0] if output_names else "Sortie non détectée")
    inputs = f"{input_count} entrée(s) détectée(s)" if input_count else "Entrée non détectée"
    return server, output, inputs


def _controller_details() -> str:
    devices = _read("/proc/bus/input/devices")
    names: list[str] = []
    for block in devices.split("\n\n"):
        name_match = re.search(r'^N:\s+Name="([^"]+)"', block, re.MULTILINE)
        if not name_match:
            continue
        name = name_match.group(1)
        if re.search(r"gamepad|controller|joystick|xbox|dualsense|dualshock|joy-con|steam deck", name, re.IGNORECASE):
            if name not in names:
                names.append(name)
    return " · ".join(names) if names else "Aucune manette détectée"


def _network_details() -> str:
    output = _run(["ip", "-brief", "address"], timeout=1.5)
    if not output:
        return "État réseau indisponible"
    entries: list[str] = []
    for line in output.splitlines():
        columns = line.split()
        if len(columns) < 2 or columns[0] == "lo":
            continue
        interface, state = columns[0], columns[1]
        addresses = [value for value in columns[2:] if "/" in value]
        address_text = ", ".join(addresses) if addresses else "Aucune adresse IP"
        entries.append(f"{interface} · {state.lower()} · {address_text}")
    return " | ".join(entries) if entries else "Aucune interface réseau détectée"


def _battery_details() -> str:
    try:
        batteries = sorted(Path("/sys/class/power_supply").glob("*/capacity"))
    except OSError:
        batteries = []
    for capacity_path in batteries:
        if not capacity_path.parent.name.lower().startswith("bat"):
            continue
        raw = _read(capacity_path).strip()
        try:
            percentage = max(0, min(100, int(raw)))
        except ValueError:
            continue
        status = _read(capacity_path.parent / "status").strip()
        suffix = f" · {status.lower()}" if status else ""
        return f"{percentage}%{suffix}"
    return "Aucune batterie détectée"


def _usb_details() -> str:
    try:
        devices = sorted(Path("/sys/bus/usb/devices").glob("*"))
    except OSError:
        devices = []
    names: list[str] = []
    for device in devices:
        product = _read(device / "product").strip()
        if not product:
            continue
        manufacturer = _read(device / "manufacturer").strip()
        label = f"{manufacturer} {product}".strip() if manufacturer else product
        if label not in names:
            names.append(label)
    return " · ".join(names[:8]) if names else "Aucun périphérique USB listé"


def collect_hardware_snapshot() -> dict[str, str]:
    """Collect one consistent UI snapshot without changing system state."""
    cpu, threads = _cpu_details()
    try:
        usage = shutil.disk_usage("/")
        gib = 1024 ** 3
        storage = f"{(usage.used / gib):.1f} / {(usage.total / gib):.1f} Gio utilisés"
    except OSError:
        storage = "Indisponible"
    bluetooth, bluetooth_devices = _bluetooth_details()
    audio_server, audio_output, audio_inputs = _audio_details()
    os_release = _read("/etc/os-release")
    pretty_name = re.search(r'^PRETTY_NAME="?([^"\n]+)', os_release, re.MULTILINE)
    return {
        "cpu": cpu,
        "cpuThreads": threads,
        "memory": _memory_details(),
        "storage": storage,
        "gpu": _gpu_details(),
        "operatingSystem": pretty_name.group(1) if pretty_name else "Linux (distribution non identifiée)",
        "kernel": platform.release() or "Indisponible",
        "bluetooth": bluetooth,
        "bluetoothDevices": bluetooth_devices,
        "audioServer": audio_server,
        "audioOutput": audio_output,
        "audioInputs": audio_inputs,
        "controllers": _controller_details(),
        "battery": _battery_details(),
        "usbDevices": _usb_details(),
        "network": _network_details(),
    }
