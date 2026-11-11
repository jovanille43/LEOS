"""Read-only system diagnostics for the LEOS Control Center."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def _run(command: Sequence[str], timeout: float = 2.5) -> str:
    """Run a bounded diagnostic query without changing system state."""
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


def _memory_percent() -> float | None:
    values: dict[str, int] = {}
    for line in _read("/proc/meminfo").splitlines():
        match = re.match(r"^(MemTotal|MemAvailable):\s+(\d+)\s+kB", line)
        if match:
            values[match.group(1)] = int(match.group(2))
    total = values.get("MemTotal", 0)
    if total <= 0 or "MemAvailable" not in values:
        return None
    return max(0.0, min(100.0, (total - values["MemAvailable"]) * 100 / total))


def _temperature_celsius() -> float | None:
    readings: list[float] = []
    try:
        zones = sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp"))
    except OSError:
        zones = []
    for path in zones:
        raw = _read(path).strip()
        try:
            value = float(raw)
        except ValueError:
            continue
        if value > 1000:
            value /= 1000.0
        if 0 < value < 150:
            readings.append(value)
    return max(readings) if readings else None


def _failed_services() -> tuple[str, list[str]]:
    output = _run(["systemctl", "--failed", "--no-legend", "--plain", "--no-pager"])
    if not output:
        return "État des services indisponible", []
    services = []
    for line in output.splitlines():
        columns = line.split()
        if len(columns) < 4:
            continue
        unit, _load, active, sub = columns[:4]
        if (
            unit.endswith((".service", ".mount", ".socket", ".timer", ".target"))
            and (active == "failed" or sub == "failed")
        ):
            services.append(unit)
    if services:
        return f"{len(services)} unité(s) en échec", services[:8]
    return "Aucune unité en échec", []


def _recent_error_count() -> str:
    output = _run([
        "journalctl", "--since=-1h", "--priority=err", "--no-pager",
        "--quiet", "--output=cat", "-n", "50",
    ], timeout=3.0)
    if not output:
        return "Journaux indisponibles ou aucune erreur lisible"
    count = sum(1 for line in output.splitlines() if line.strip())
    return f"{count} entrée(s) d'erreur récente(s), maximum 50 affichées par la sonde"


def _uptime() -> str:
    raw = _read("/proc/uptime").split()
    if not raw:
        return "Indisponible"
    try:
        seconds = max(0, int(float(raw[0])))
    except (ValueError, OverflowError):
        return "Indisponible"
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days} j {hours} h"
    if hours:
        return f"{hours} h {minutes} min"
    return f"{minutes} min"


def _top_processes() -> list[dict[str, str]]:
    output = _run([
        "ps", "-eo", "pid=,comm=,%cpu=,%mem=,rss=", "--sort=-%cpu",
    ], timeout=2.0)
    processes: list[dict[str, str]] = []
    for line in output.splitlines():
        columns = line.split(None, 4)
        if len(columns) < 5:
            continue
        pid, name, cpu, memory, rss = columns
        try:
            cpu_value = float(cpu)
            memory_value = float(memory)
            memory_mib = int(rss) / 1024
        except ValueError:
            continue
        processes.append({
            "pid": pid,
            "name": name[:40],
            "cpu": f"{cpu_value:.1f}%",
            "memory": f"{memory_value:.1f}%",
            "resident": f"{memory_mib:.0f} Mio",
        })
        if len(processes) >= 8:
            break
    return processes


def collect_system_diagnostics() -> dict[str, object]:
    """Return a compact health report; never repair or restart anything."""
    findings: list[str] = []
    severity = "OK"

    try:
        usage = shutil.disk_usage("/")
        storage_percent = usage.used * 100 / usage.total if usage.total else 0.0
    except OSError:
        storage_percent = None

    memory_percent = _memory_percent()
    temperature = _temperature_celsius()
    failed_summary, failed_services = _failed_services()
    recent_errors = _recent_error_count()

    if storage_percent is not None and storage_percent >= 90:
        findings.append(f"Espace disque critique : {storage_percent:.0f}% occupés sur /.")
        severity = "Critique"
    elif storage_percent is not None and storage_percent >= 80:
        findings.append(f"Espace disque élevé : {storage_percent:.0f}% occupés sur /.")
        severity = "Attention"

    if memory_percent is not None and memory_percent >= 92:
        findings.append(f"Utilisation mémoire élevée : {memory_percent:.0f}%.")
        severity = "Critique"
    elif memory_percent is not None and memory_percent >= 85:
        findings.append(f"Utilisation mémoire à surveiller : {memory_percent:.0f}%.")
        if severity == "OK":
            severity = "Attention"

    if temperature is not None and temperature >= 90:
        findings.append(f"Température maximale exposée par le noyau : {temperature:.0f} °C.")
        severity = "Critique"
    elif temperature is not None and temperature >= 80:
        findings.append(f"Température élevée à surveiller : {temperature:.0f} °C.")
        if severity == "OK":
            severity = "Attention"

    if failed_services:
        findings.append("Des unités systemd sont en échec : " + ", ".join(failed_services) + ".")
        severity = "Critique" if severity == "OK" else severity

    if not findings:
        findings.append("Aucune anomalie détectée par les contrôles disponibles.")

    try:
        load = os.getloadavg()
        cpu_count = os.cpu_count() or 1
        load_text = f"{load[0]:.2f} · {load[1]:.2f} · {load[2]:.2f} (1/5/15 min, {cpu_count} CPU logiques)"
    except (OSError, AttributeError):
        load_text = "Indisponible"

    return {
        "severity": severity,
        "summary": (
            "Les contrôles disponibles n'ont détecté aucune anomalie."
            if severity == "OK"
            else "Des points nécessitent ton attention ; consulte les détails avant toute action."
        ),
        "findings": findings,
        "storage": f"{storage_percent:.0f}% utilisés sur /" if storage_percent is not None else "Indisponible",
        "memory": f"{memory_percent:.0f}% utilisée" if memory_percent is not None else "Indisponible",
        "temperature": f"{temperature:.0f} °C (maximum exposé)" if temperature is not None else "Capteur indisponible",
        "failedServices": failed_summary,
        "failedServiceNames": failed_services,
        "recentErrors": recent_errors,
        "uptime": _uptime(),
        "loadAverage": load_text,
        "topProcesses": _top_processes(),
    }
