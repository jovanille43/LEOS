"""Read-only inspection and guarded eligibility planning for KDE Plasma layouts.

This module never writes to Plasma configuration. It inventories panel
containments, records the source fingerprint, and decides whether the saved
LEOS dock profile can be offered for explicit, backed-up application.
"""
from __future__ import annotations

import configparser
import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Any

from desktop.layouts import validate_layout
from desktop.plasma_adapter import LEOS_PANEL_MARKER
from desktop.plasma_backup import MAX_BACKUP_BYTES, _config_root

_SECTION = re.compile(r"^Containments\]\[(?P<id>\d+)(?:\]\[(?P<nested>.*))?$")
_APPLET = re.compile(r"^Applets\]\[(?P<id>\d+)(?:\]|$)")


def _default_config_path() -> Path:
    return _config_root() / "plasma-org.kde.plasma.desktop-appletsrc"


def _read_config_snapshot(path: Path) -> tuple[bytes, str | None]:
    """Read a bounded regular file without following a symlink where supported."""
    if path.is_symlink():
        return b"", "unsafe"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            return b"", "unsafe"
        if info.st_size <= 0 or info.st_size > MAX_BACKUP_BYTES:
            return b"", "unsupported-size"
        chunks: list[bytes] = []
        remaining = MAX_BACKUP_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(data) > MAX_BACKUP_BYTES
            or len(data) != info.st_size
            or info.st_ino != after.st_ino
            or info.st_size != after.st_size
            or info.st_mtime_ns != after.st_mtime_ns
        ):
            return b"", "changed-during-read"
        return data, None
    finally:
        os.close(descriptor)


def inspect_plasma_config(path: Path | None = None) -> dict[str, Any]:
    """Inspect the current Plasma applet configuration without modifying it."""
    source = path or _default_config_path()
    try:
        data, failure = _read_config_snapshot(source)
    except FileNotFoundError:
        return {"status": "missing", "available": False, "panels": [], "containments": [],
                "warnings": ["Fichier de configuration Plasma absent."]}
    except PermissionError:
        return {"status": "unreadable", "available": False, "panels": [], "containments": [],
                "warnings": ["Accès en lecture refusé."]}
    except OSError:
        return {"status": "unreadable", "available": False, "panels": [], "containments": [],
                "warnings": ["Impossible de lire la configuration Plasma."]}

    if failure:
        messages = {
            "unsafe": "Le fichier n'est pas un fichier régulier sûr à inspecter.",
            "unsupported-size": "La taille du fichier n'est pas prise en charge.",
            "changed-during-read": "La configuration a changé pendant l'inspection ; recommencer.",
        }
        return {"status": failure, "available": False, "panels": [], "containments": [],
                "warnings": [messages.get(failure, "Inspection impossible.")]}

    try:
        text = data.decode("utf-8")
        parser = configparser.ConfigParser(interpolation=None, strict=False, allow_no_value=True)
        parser.optionxform = str
        parser.read_string(text)
    except (UnicodeDecodeError, configparser.Error):
        return {"status": "invalid", "available": False, "panels": [], "containments": [],
                "warnings": ["Le fichier n'est pas un fichier INI Plasma valide ou lisible en UTF-8."]}

    grouped: dict[str, dict[str, Any]] = {}
    for section in parser.sections():
        match = _SECTION.fullmatch(section)
        if not match:
            continue
        containment_id = match.group("id")
        nested = match.group("nested")
        item = grouped.setdefault(containment_id, {"id": containment_id, "plugin": None,
                                                    "location": None, "formfactor": None,
                                                    "applets": [], "leos_managed": False})
        values = parser[section]
        if nested is None:
            item["plugin"] = values.get("plugin")
            item["location"] = values.get("location")
            item["formfactor"] = values.get("formfactor")
        else:
            if nested == "LEOS":
                item["leos_managed"] = values.get("managedBy") == LEOS_PANEL_MARKER
            applet_match = _APPLET.match(nested)
            if applet_match and values.get("plugin"):
                item["applets"].append({
                    "id": applet_match.group("id"),
                    "plugin": values.get("plugin"),
                })

    containments = sorted(grouped.values(), key=lambda value: int(value["id"]))
    panels = [
        item for item in containments
        if isinstance(item.get("plugin"), str)
        and item["plugin"].strip().lower() in {
            "org.kde.plasma.panel",
            "org.kde.plasma.pagerpanel",
        }
    ]
    for item in containments:
        item["applets"].sort(key=lambda value: int(value["id"]))

    return {
        "status": "ready",
        "available": True,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "containment_count": len(containments),
        "panel_count": len(panels),
        "panels": panels,
        "containments": containments,
        "warnings": [] if panels else ["Aucun panneau Plasma standard n'a été identifié."],
    }


def build_layout_plan(layout: object, inspection: dict[str, Any]) -> dict[str, Any]:
    """Prepare a guarded application plan; never modify Plasma from this module."""
    if not validate_layout(layout):
        raise ValueError("Invalid LEOS desktop layout")
    assert isinstance(layout, dict)
    dock = dict(layout["dock"])
    panels = inspection.get("panels", []) if inspection.get("available") else []
    observations: list[str] = []
    blocked_reason = ""

    if not inspection.get("available"):
        blocked_reason = "La configuration Plasma n'a pas pu être inspectée ; application bloquée."
        observations.append("La configuration Plasma n'a pas pu être inspectée ; sauvegarde et contrôle manuel requis.")
    elif not dock["enabled"]:
        blocked_reason = "Le dock est désactivé dans les préférences LEOS ; aucun panneau ne sera supprimé."
        observations.append("Le dock LEOS est désactivé dans les préférences ; les panneaux KDE existants resteront intacts.")
    elif layout["widgets_enabled"]:
        blocked_reason = "Les widgets du bureau ne sont pas encore intégrés à l'application des profils."
        observations.append("Les widgets du bureau sont activés dans le profil, mais leur intégration reste à terminer.")
    elif len(panels) > 1:
        blocked_reason = "Plusieurs panneaux KDE sont présents ; la disposition multi-panneaux est laissée intacte."
        observations.append("Plusieurs panneaux KDE ont été détectés ; LEOS refuse de choisir lequel modifier.")
    elif len(panels) == 1:
        panel = panels[0]
        if panel.get("leos_managed"):
            observations.append("Le panneau LEOS existant sera actualisé.")
        else:
            observations.append(
                "Un panneau KDE personnel unique sera réutilisé après confirmation ; ses applets existants seront conservés."
            )
        observations.append("Seuls la position, l'alignement, la hauteur et le masquage automatique seront ajustés.")
    else:
        observations.append("Aucun panneau Plasma standard détecté ; un nouveau panneau LEOS pourra être créé.")

    can_apply = not blocked_reason
    if can_apply:
        observations.append("Le profil peut être appliqué après confirmation explicite et création d'une sauvegarde.")
    else:
        observations.append("Aucune modification ne sera effectuée tant que le point bloquant n'est pas résolu.")

    return {
        "schema_version": 1,
        "mode": "ready-for-confirmation" if can_apply else "preview-only",
        "can_apply": can_apply,
        "requires_backup": True,
        "desired": {
            "profile": layout["profile"],
            "dock": dock,
            "widgets_enabled": layout["widgets_enabled"],
        },
        "detected_panel_count": len(panels),
        "observations": observations,
        "blocked_reason": blocked_reason,
    }

def format_layout_report(inspection: dict[str, Any], plan: dict[str, Any]) -> str:
    """Create a compact French report suitable for the Control Center."""
    lines = ["ANALYSE KDE — LECTURE SEULE"]
    status = inspection.get("status")
    if status == "ready":
        lines.append(
            f"Configuration lue : {inspection.get('containment_count', 0)} conteneur(s), "
            f"{inspection.get('panel_count', 0)} panneau(x)."
        )
        digest = inspection.get("sha256", "")
        if digest:
            lines.append(f"Empreinte SHA-256 : {digest[:16]}…")
        for panel in inspection.get("panels", []):
            applets = ", ".join(item["plugin"] for item in panel.get("applets", [])) or "aucun applet identifié"
            ownership = "géré par LEOS" if panel.get("leos_managed") else "panneau KDE personnel"
            lines.append(
                f"Panneau {panel['id']} ({ownership}) — emplacement KDE brut : "
                f"{panel.get('location') or 'inconnu'} ; formfactor : "
                f"{panel.get('formfactor') or 'inconnu'} ; applets : {applets}."
            )
    else:
        warning = (inspection.get("warnings") or ["État indisponible."])[0]
        lines.append(f"Inspection indisponible ({status}) : {warning}")

    lines.append("")
    lines.append("APERÇU DU PROFIL LEOS")
    lines.extend(f"• {item}" for item in plan["observations"])
    if plan["blocked_reason"]:
        lines.append(plan["blocked_reason"])
    else:
        lines.append("Prêt pour une application après confirmation explicite.")
    lines.append("Aucune modification du bureau n'a été effectuée pendant cette analyse.")
    return "\n".join(lines)
