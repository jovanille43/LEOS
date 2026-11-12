"""Read-only hardware and peripheral inventory for the LEOS Control Center."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence


MAX_HARDWARE_TEXT_BYTES = 4 * 1024 * 1024


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
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_HARDWARE_TEXT_BYTES + 1)
    except OSError:
        return ""
    if len(raw) > MAX_HARDWARE_TEXT_BYTES:
        return ""
    return raw.decode("utf-8", errors="replace")


def _cpu_details() -> tuple[str, str]:
    """Identify CPU models and logical threads across x86 and ARM Linux systems."""
    data = _read("/proc/cpuinfo")
    model = ""
    processor_entries = 0
    model_fields = {"model name", "hardware", "processor", "model"}

    for line in data.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue

        if key == "processor":
            # ARM commonly uses numeric processor IDs, but some systems put
            # the human-readable CPU model in this same field.
            if value.isdigit():
                processor_entries += 1
            elif not model:
                model = value.strip("\x00")
        elif key in model_fields and not model:
            candidate = value.strip("\x00")
            if candidate.lower() not in {"0", "unknown", "not specified"}:
                model = candidate

    if not model:
        for path in (
            "/sys/firmware/devicetree/base/model",
            "/sys/devices/virtual/dmi/id/product_name",
            "/sys/devices/virtual/dmi/id/board_name",
        ):
            candidate = _read(path).replace("\x00", "").strip()
            if candidate and candidate.lower() not in {"unknown", "not specified"}:
                model = candidate
                break

    online = _read("/sys/devices/system/cpu/online")
    online_ids = _parse_cpu_list(online) if online else set()
    logical = len(online_ids) or processor_entries or os.cpu_count() or 0
    return model or "Non détecté", f"{logical} thread(s)" if logical else "Indisponible"

def _parse_cpu_list(value: str) -> set[int]:
    """Parse Linux CPU-list syntax such as '0-3,8,10-11'."""
    cpus: set[int] = set()
    for item in value.strip().split(","):
        if not item:
            continue
        try:
            if "-" in item:
                first, last = (int(part) for part in item.split("-", 1))
                if first < 0 or last < first:
                    continue
                cpus.update(range(first, last + 1))
            else:
                cpu = int(item)
                if cpu >= 0:
                    cpus.add(cpu)
        except ValueError:
            continue
    return cpus


def _cpu_topology_from_sysfs(root: Path) -> tuple[int | None, int]:
    """Read online CPU/core topology from sysfs, which also supports non-x86 CPUs."""
    online = _read(root / "online")
    online_ids = _parse_cpu_list(online) if online else set()
    if not online_ids:
        online_ids = {
            int(match.group(1))
            for path in root.glob("cpu[0-9]*")
            if (match := re.fullmatch(r"cpu(\d+)", path.name))
        }

    core_pairs: set[tuple[str, str]] = set()
    core_ids: set[str] = set()
    for cpu_id in online_ids:
        topology = root / f"cpu{cpu_id}" / "topology"
        core = _read(topology / "core_id").strip()
        package = _read(topology / "physical_package_id").strip()
        # Some ARM systems expose cluster_id rather than a physical package ID.
        # Pairing it with core_id avoids merging cores that reuse IDs in clusters.
        cluster = _read(topology / "cluster_id").strip()
        if not core:
            continue
        grouping = package or cluster
        if grouping:
            core_pairs.add((grouping, core))
        else:
            core_ids.add(core)

    if core_pairs:
        return len(core_pairs), len(online_ids)
    if core_ids:
        return len(core_ids), len(online_ids)
    return None, len(online_ids)


def _cpu_topology(
    data: str | None = None,
    sysfs_root: Path = Path("/sys/devices/system/cpu"),
) -> tuple[int | None, int]:
    """Estimate physical cores from sysfs or /proc without guessing from threads."""
    if data is None:
        physical_cores, logical_threads = _cpu_topology_from_sysfs(sysfs_root)
        if physical_cores is not None:
            return physical_cores, logical_threads or os.cpu_count() or 0
        cpu_data = _read("/proc/cpuinfo")
    else:
        # Explicit data keeps this parser deterministic for tests and callers.
        cpu_data = data

    blocks = re.split(r"\n\s*\n", cpu_data.strip()) if cpu_data.strip() else []
    logical_ids: set[str] = set()
    core_pairs: set[tuple[str, str]] = set()
    core_ids: set[str] = set()

    for block in blocks:
        processor = re.search(r"^processor\s*:\s*(\S+)", block, re.MULTILINE)
        package = re.search(r"^physical id\s*:\s*(\S+)", block, re.MULTILINE)
        core = re.search(r"^core id\s*:\s*(\S+)", block, re.MULTILINE)
        if processor:
            logical_ids.add(processor.group(1))
        if package and core:
            core_pairs.add((package.group(1), core.group(1)))
        elif core:
            core_ids.add(core.group(1))

    physical_cores = len(core_pairs) if core_pairs else (len(core_ids) if core_ids else None)
    logical_threads = len(logical_ids) or os.cpu_count() or 0
    return physical_cores, logical_threads


def _cpu_core_details(physical_cores: int | None, logical_threads: int) -> str:
    if physical_cores is None:
        return "Cœurs physiques indisponibles"
    suffix = f" · {logical_threads} threads logiques" if logical_threads else ""
    return f"{physical_cores} cœur(s) physique(s) estimé(s){suffix}"


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


def _memory_total_bytes() -> int:
    """Return physical RAM in bytes, or zero when the kernel does not expose it."""
    match = re.search(r"^MemTotal:\s+(\d+)\s+kB", _read("/proc/meminfo"), re.MULTILINE)
    return int(match.group(1)) * 1024 if match else 0


def _memory_total_details(total_bytes: int) -> str:
    if total_bytes <= 0:
        return "Indisponible"
    return f"{total_bytes / (1024 ** 3):.1f} Gio"


def _storage_details() -> tuple[str, int | None]:
    """Report free space on /; this does not identify the physical drive type."""
    try:
        usage = shutil.disk_usage("/")
    except OSError:
        return "Indisponible", None
    gib = 1024 ** 3
    return (
        f"{usage.used / gib:.1f} / {usage.total / gib:.1f} Gio utilisés · "
        f"{usage.free / gib:.1f} Gio libres sur /",
        usage.free,
    )


def _parse_vulkan_devices(output: str) -> list[tuple[str, tuple[int, int, int] | None]]:
    """Parse per-device Vulkan API versions from vulkaninfo --summary."""
    sections = re.split(r"(?m)^\s*GPU\d+\s*:\s*$", output)
    devices: list[tuple[str, tuple[int, int, int] | None]] = []
    for section in sections[1:]:
        name_match = re.search(r"^\s*deviceName\s*=\s*(.+?)\s*$", section, re.MULTILINE)
        if not name_match:
            continue
        version_match = re.search(
            r"^\s*apiVersion\s*=\s*(\d+)\.(\d+)\.(\d+)",
            section,
            re.MULTILINE,
        )
        version = (
            tuple(int(part) for part in version_match.groups())
            if version_match
            else None
        )
        devices.append((name_match.group(1).strip().strip('"'), version))
    return devices


def _vulkan_snapshot() -> tuple[str, list[tuple[str, tuple[int, int, int] | None]] | None]:
    """Read the actual per-GPU Vulkan API version when vulkaninfo is available."""
    if not shutil.which("vulkaninfo"):
        return "Non vérifiable (outil vulkaninfo absent)", None
    output = _run(["vulkaninfo", "--summary"], timeout=4.0)
    if not output:
        return "Non vérifiable (Vulkan ou pilote non exposé)", None
    devices = _parse_vulkan_devices(output)
    if not devices:
        return "GPU Vulkan non détaillé par le pilote", None

    labels = []
    for name, version in devices:
        if version is None:
            labels.append(f"{name} · version Vulkan inconnue")
        else:
            labels.append(f"{name} · Vulkan {'.'.join(str(part) for part in version)}")
    return " | ".join(labels), devices


def _architecture_details(machine: str | None = None) -> str:
    """Normalize common machine names without implying unsupported architectures work."""
    value = (platform.machine() if machine is None else machine).strip().lower()
    if value in {"x86_64", "amd64", "x64"}:
        return "x86_64"
    if value in {"aarch64", "arm64"}:
        return "ARM64"
    return value or "Indisponible"


def _firmware_details(path: Path = Path("/sys/firmware/efi")) -> str:
    """UEFI is detected only when Linux exposes its EFI firmware interface."""
    try:
        return "UEFI" if path.is_dir() else "UEFI non détecté"
    except OSError:
        return "Indisponible"


def _gaming_baseline_assessment(
    architecture: str,
    firmware: str,
    memory_total_bytes: int,
    physical_cores: int | None = None,
    storage_free_bytes: int | None = None,
    vulkan_devices: list[tuple[str, tuple[int, int, int] | None]] | None = None,
) -> str:
    """Compare observable values with Bazzite's Gaming reference, without certifying a PC."""
    issues: list[str] = []
    unknown: list[str] = []

    if architecture == "Indisponible":
        unknown.append("architecture non vérifiable")
    elif architecture != "x86_64":
        issues.append(f"architecture {architecture} hors cible x86_64")

    if firmware == "Indisponible":
        unknown.append("mode de démarrage non vérifiable")
    elif firmware != "UEFI":
        issues.append("démarrage UEFI non détecté")

    if memory_total_bytes <= 0:
        unknown.append("quantité de RAM non vérifiable")
    elif memory_total_bytes < 8_000_000_000:
        issues.append("moins de 8 Go de RAM")

    if physical_cores is None:
        unknown.append("nombre de cœurs physiques non vérifiable")
    elif physical_cores < 4:
        issues.append("moins de 4 cœurs physiques détectés")

    if storage_free_bytes is None:
        unknown.append("espace libre sur / non vérifiable")
    elif storage_free_bytes < 50_000_000_000:
        issues.append("moins de 50 Go libres sur /")

    if not vulkan_devices:
        unknown.append("prise en charge Vulkan 1.3+ non vérifiable")
    else:
        known_versions = [version for _name, version in vulkan_devices if version is not None]
        if any(version >= (1, 3, 0) for version in known_versions):
            pass
        elif len(known_versions) == len(vulkan_devices):
            issues.append("aucun GPU détecté n'expose Vulkan 1.3+")
        else:
            unknown.append("version Vulkan insuffisamment exposée par le pilote")

    # The published CPU frequency and internal SSD requirements cannot be proven
    # reliably from a desktop session, so the dashboard never labels them certified.
    unknown.extend(["fréquence CPU de référence non certifiée", "type de support de stockage non vérifié"])

    if issues:
        message = "Sous le seuil Gaming de référence : " + " · ".join(issues)
        if unknown:
            message += ". À confirmer : " + " · ".join(unknown)
        return message
    if unknown:
        unverified_only = {
            "fréquence CPU de référence non certifiée",
            "type de support de stockage non vérifié",
        }
        if set(unknown).issubset(unverified_only):
            return "Indicateurs vérifiables au niveau des seuils. Non certifié : " + " · ".join(unknown)
        return "Contrôle Gaming incomplet. À confirmer : " + " · ".join(unknown)
    return (
        "Seuils matériels Gaming observés comme conformes. "
        "Cela ne remplace pas un essai réel des pilotes, du Wi-Fi, de l'audio et des jeux."
    )

def _parse_lspci_gpu_devices(output: str) -> dict[str, str]:
    """Map PCI addresses to descriptive GPU names from lspci output."""
    devices: dict[str, str] = {}
    pattern = re.compile(
        r"^([0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7])\s+"
        r"(?:VGA compatible controller|3D controller|Display controller)"
        r"(?:\s+\[[^]]+\])?:\s*(.+)$",
        re.IGNORECASE,
    )
    for line in output.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        description = re.sub(
            r"\s+\[[0-9a-f]{4}:[0-9a-f]{4}\](?:\s+\(rev [^)]+\))?$",
            "",
            match.group(2).strip(),
            flags=re.IGNORECASE,
        )
        if description:
            devices[match.group(1).lower()] = description
    return devices


def _gpu_details() -> str:
    records: list[tuple[str, str, str]] = []
    seen_devices: set[str] = set()
    vendor_names = {"0x10de": "NVIDIA", "0x1002": "AMD", "0x8086": "Intel"}
    pci_output = _run(["lspci", "-D", "-nn"], timeout=2.0)
    pci_names = _parse_lspci_gpu_devices(pci_output)
    pci_pattern = re.compile(
        r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\\.[0-7]$",
        re.IGNORECASE,
    )
    try:
        devices = sorted(
            device
            for device in Path("/sys/class/drm").glob("card*/device")
            if re.fullmatch(r"card\\d+", device.parent.name)
        )
    except OSError:
        devices = []

    for device in devices:
        vendor = _read(device / "vendor").strip().lower()
        if not vendor:
            continue
        vendor_name = vendor_names.get(vendor, f"GPU {vendor}")
        try:
            resolved = device.resolve(strict=True)
        except OSError:
            resolved = device
        pci_address = ""
        for parent in (resolved, *resolved.parents):
            if pci_pattern.fullmatch(parent.name):
                pci_address = parent.name.lower()
                break

        # DRM card numbers can change between boots. PCI identity is the
        # stable key for PCI GPUs; the resolved path is a conservative fallback.
        identity = pci_address or str(resolved)
        if identity in seen_devices:
            continue
        seen_devices.add(identity)

        name = pci_names.get(pci_address, vendor_name)
        driver_link = device / "driver"
        try:
            driver = driver_link.resolve(strict=True).name
        except OSError:
            driver = ""
        label = f"{name} ({driver})" if driver else name
        records.append((label, pci_address, device.parent.name))

    if records:
        label_counts: dict[str, int] = {}
        for label, _pci_address, _drm_card in records:
            label_counts[label] = label_counts.get(label, 0) + 1

        found = []
        for label, pci_address, drm_card in records:
            if label_counts[label] > 1:
                location = pci_address or drm_card
                found.append(f"{label} [{location}]")
            else:
                found.append(label)
        return " · ".join(found)

    lines = [
        line.split(": ", 1)[-1]
        for line in pci_output.splitlines()
        if "VGA compatible controller" in line
        or "3D controller" in line
        or "Display controller" in line
    ]
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
    input_count = 0
    for line in sources.splitlines():
        columns = line.split()
        if len(columns) >= 2 and not columns[1].endswith(".monitor"):
            input_count += 1
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
    """Collect one consistent, read-only UI snapshot without changing system state."""
    cpu, threads = _cpu_details()
    physical_cores, logical_threads = _cpu_topology()
    storage, storage_free_bytes = _storage_details()
    bluetooth, bluetooth_devices = _bluetooth_details()
    audio_server, audio_output, audio_inputs = _audio_details()
    architecture = _architecture_details()
    firmware = _firmware_details()
    memory_total_bytes = _memory_total_bytes()
    vulkan, vulkan_devices = _vulkan_snapshot()
    os_release = _read("/etc/os-release")
    pretty_name = re.search(r'^PRETTY_NAME="?([^"\n]+)', os_release, re.MULTILINE)
    return {
        "cpu": cpu,
        "cpuThreads": threads,
        "cpuCores": _cpu_core_details(physical_cores, logical_threads),
        "memory": _memory_details(),
        "memoryTotal": _memory_total_details(memory_total_bytes),
        "architecture": architecture,
        "firmware": firmware,
        "gamingBaseline": _gaming_baseline_assessment(
            architecture,
            firmware,
            memory_total_bytes,
            physical_cores,
            storage_free_bytes,
            vulkan_devices,
        ),
        "storage": storage,
        "gpu": _gpu_details(),
        "vulkan": vulkan,
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
