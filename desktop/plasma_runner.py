"""Run an explicitly approved Plasma script through the user's session D-Bus.

The runner is deliberately narrow: it can invoke only PlasmaShell.evaluateScript,
uses argv rather than a shell, and enforces a script size and execution timeout.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Callable

MAX_PLASMA_SCRIPT_BYTES = 256 * 1024
PLASMA_SERVICE = "org.kde.plasmashell"
PLASMA_OBJECT = "/PlasmaShell"
PLASMA_INTERFACE = "org.kde.PlasmaShell"
PLASMA_METHOD = "evaluateScript"


def plasma_script_command(script: str, executable: str | None = None) -> list[str] | None:
    """Build the fixed busctl invocation, or return None when busctl is absent."""
    if not isinstance(script, str) or not script.strip() or "\x00" in script:
        raise ValueError("A non-empty Plasma script is required")
    if len(script.encode("utf-8")) > MAX_PLASMA_SCRIPT_BYTES:
        raise ValueError("Plasma script exceeds the supported size")
    binary = executable if executable is not None else shutil.which("busctl")
    if not binary:
        return None
    return [
        binary, "--user", "call", PLASMA_SERVICE, PLASMA_OBJECT,
        PLASMA_INTERFACE, PLASMA_METHOD, "s", script,
    ]


def execute_plasma_script(
    script: str,
    *,
    timeout: float = 30.0,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    executable: str | None = None,
) -> tuple[bool, str]:
    """Execute a bounded Plasma script and return a user-safe result message."""
    if timeout <= 0 or timeout > 120:
        raise ValueError("Plasma script timeout is outside the supported range")
    binary = executable if executable is not None else shutil.which("busctl")
    command = plasma_script_command(script, binary)
    if command is None:
        return False, "L'outil busctl est introuvable sur cette session."
    run = runner or subprocess.run
    try:
        result = run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return False, "L'outil busctl est introuvable sur cette session."
    except subprocess.TimeoutExpired:
        return False, "Plasma n'a pas répondu dans le délai autorisé."
    except OSError:
        return False, "Impossible de contacter le service Plasma."

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().replace("\n", " ")
        if len(detail) > 360:
            detail = detail[:357] + "..."
        message = "Plasma a refusé le script."
        if detail:
            message += f" Détail : {detail}"
        return False, message
    return True, "La commande a été acceptée par Plasma."
