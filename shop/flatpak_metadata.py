"""Small, defensive readers for Flatpak application metadata."""

from __future__ import annotations

import re


_RUNTIME_REF_RE = re.compile(
    r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)


def application_runtime(metadata: str) -> str:
    """Return the declared Application runtime ref, if it is well-formed."""
    if not isinstance(metadata, str):
        return ""
    in_application = False
    for raw_line in metadata.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_application = line[1:-1].strip().casefold() == "application"
            continue
        if not in_application or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().casefold() != "runtime":
            continue
        runtime = value.strip()
        return runtime if _RUNTIME_REF_RE.fullmatch(runtime) else ""
    return ""


def runtime_summary(metadata: str) -> str:
    """Create an honest user-facing summary without claiming all dependencies are known."""
    runtime = application_runtime(metadata)
    if runtime:
        return (
            f"Runtime déclaré par l'application : {runtime}. "
            "Flatpak vérifiera et installera les composants nécessaires si besoin."
        )
    return (
        "Aucun runtime explicite n'a été trouvé dans les métadonnées. "
        "Flatpak résoudra les dépendances au moment de l'installation."
    )
