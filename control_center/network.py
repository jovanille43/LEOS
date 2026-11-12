"""Read-only network status and interface throughput for LEOS."""

from __future__ import annotations

import ipaddress
import re
import subprocess
from pathlib import Path
from typing import Mapping


def _read(path: str | Path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _run(command: list[str], timeout: float = 2.0) -> str:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def _default_route() -> tuple[str, str]:
    """Return an active IPv4 or IPv6 default interface and its gateway."""
    for line in _read("/proc/net/route").splitlines()[1:]:
        columns = line.split()
        if len(columns) < 4 or columns[1] != "00000000":
            continue
        try:
            flags = int(columns[3], 16)
            if not flags & 0x1:
                continue
            gateway = ""
            if flags & 0x2:
                gateway_int = int(columns[2], 16)
                gateway = ".".join(
                    str((gateway_int >> (8 * i)) & 255) for i in range(4)
                )
            return columns[0], gateway
        except (ValueError, IndexError):
            continue

    # IPv6 routes are exposed separately by Linux and are essential on
    # IPv6-only networks where /proc/net/route has no default route.
    for line in _read("/proc/net/ipv6_route").splitlines():
        columns = line.split()
        if (
            len(columns) < 10
            or columns[0] != "0" * 32
            or columns[1] != "00"
        ):
            continue
        try:
            flags = int(columns[8], 16)
            if not flags & 0x1:
                continue
            gateway_bytes = bytes.fromhex(columns[4])
            gateway_address = ipaddress.IPv6Address(gateway_bytes)
            gateway = "" if gateway_address.is_unspecified else str(gateway_address)
            return columns[9], gateway
        except (ValueError, IndexError):
            continue
    return "", ""

def _dns_servers() -> list[str]:
    servers: list[str] = []
    for line in _read("/etc/resolv.conf").splitlines():
        match = re.match(r"\s*nameserver\s+(\S+)", line)
        if match and match.group(1) not in servers:
            servers.append(match.group(1))
    return servers[:4]


def _wireless_details(interface: str) -> dict[str, str]:
    if not interface:
        return {"ssid": "Non connecté", "signal": "—"}
    output = _run(["iw", "dev", interface, "link"])
    if not output or "Not connected" in output:
        return {"ssid": "Non connecté", "signal": "—"}
    ssid_match = re.search(r"^\s*SSID:\s*(.+)$", output, re.MULTILINE)
    signal_match = re.search(r"^\s*signal:\s*(-?\d+)\s*dBm", output, re.MULTILINE)
    return {
        "ssid": ssid_match.group(1).strip() if ssid_match else "Connecté",
        "signal": f"{signal_match.group(1)} dBm" if signal_match else "—",
    }


def _format_rate(value: float) -> str:
    if value < 1024:
        return f"{value:.0f} o/s"
    if value < 1024 ** 2:
        return f"{value / 1024:.1f} Ko/s"
    return f"{value / (1024 ** 2):.2f} Mo/s"


def collect_network_snapshot(
    previous: Mapping[str, tuple[int, int]] | None = None,
    elapsed_seconds: float = 0.0,
) -> dict[str, object]:
    """Collect interface counters and local network metadata without sending traffic."""
    previous = previous or {}
    interfaces: list[dict[str, str]] = []
    current: dict[str, tuple[int, int]] = {}
    root = Path("/sys/class/net")
    try:
        names = sorted(path.name for path in root.iterdir() if path.name != "lo")
    except OSError:
        names = []

    default_interface, gateway = _default_route()
    wifi = _wireless_details(default_interface)
    for name in names:
        base = root / name
        state = _read(base / "operstate").strip() or "unknown"
        try:
            rx = int(_read(base / "statistics/rx_bytes").strip())
            tx = int(_read(base / "statistics/tx_bytes").strip())
        except ValueError:
            rx = tx = 0
        current[name] = (rx, tx)
        rx_rate = tx_rate = "—"
        if elapsed_seconds > 0 and name in previous:
            old_rx, old_tx = previous[name]
            rx_rate = _format_rate(max(0, rx - old_rx) / elapsed_seconds)
            tx_rate = _format_rate(max(0, tx - old_tx) / elapsed_seconds)
        address_output = _run(["ip", "-brief", "address", "show", "dev", name])
        addresses: list[str] = []
        if address_output:
            for token in address_output.split()[2:]:
                if "/" in token and token not in addresses:
                    addresses.append(token)
        interfaces.append({
            "name": name,
            "type": "Wi-Fi" if (base / "wireless").exists() else "Ethernet",
            "state": "Connectée" if state == "up" else ("Déconnectée" if state == "down" else state),
            "addresses": ", ".join(addresses) if addresses else "Aucune adresse",
            "downloadRate": rx_rate,
            "uploadRate": tx_rate,
            "isDefault": "true" if name == default_interface else "false",
        })

    connected = any(item["state"] == "Connectée" for item in interfaces)
    return {
        "status": "Connecté" if connected and default_interface else ("Réseau local actif" if connected else "Hors ligne"),
        "defaultInterface": default_interface or "Aucune",
        "gateway": gateway or "Non détectée",
        "dns": ", ".join(_dns_servers()) or "Non détecté",
        "wifiSsid": wifi["ssid"],
        "wifiSignal": wifi["signal"],
        "interfaces": interfaces,
        "counters": current,
    }
