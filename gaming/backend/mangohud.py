"""Optional MangoHud launch integration.

MangoHud is never installed or enabled globally by LEOS. It is wrapped around
direct executable launches only; URI-based launchers such as Steam keep their
own per-game launch options.
"""
from __future__ import annotations

import shutil
from collections.abc import Sequence


def find_mangohud() -> str:
    """Return the host MangoHud executable, if installed."""
    return shutil.which("mangohud") or ""


def build_launch_command(
    launch: Sequence[str], enabled: bool, executable: str | None = None
) -> list[str]:
    """Build a safe argv list; never use a shell or rewrite URI handlers."""
    command = [str(part) for part in launch]
    if not command or not enabled:
        return command
    if "://" in command[0]:
        return command
    binary = executable if executable is not None else find_mangohud()
    if not binary:
        return command
    return [binary, *command]
