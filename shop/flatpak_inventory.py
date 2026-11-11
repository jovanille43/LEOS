"""Parse the human-readable Flatpak application inventory safely."""

from __future__ import annotations

import re


APP_ID_RE = re.compile(r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+$")


def flatpak_uninstall_args(app_id: str, scope: str) -> list[str]:
    """Build a safe Flatpak uninstall argument list for a known installation."""
    if not APP_ID_RE.fullmatch(app_id):
        raise ValueError("Invalid Flatpak application ID")
    if scope not in {"user", "system"}:
        raise ValueError("Unsupported Flatpak installation scope")
    scope_flag = "--user" if scope == "user" else "--system"
    return ["uninstall", scope_flag, "--assumeyes", app_id]


def parse_flatpak_inventory(output: str) -> tuple[set[str], set[str]]:
    """Return separate user and system app IDs from --columns output.

    Flatpak's table output includes a header. The application ID is a
    whitespace-free token; the installation column is either 'user' or a
    named/system installation.
    """
    user_apps: set[str] = set()
    system_apps: set[str] = set()
    for line in output.splitlines():
        columns = line.split()
        if len(columns) < 2:
            continue
        app_id, installation = columns[0], columns[-1]
        if app_id.casefold() in {"application", "app"}:
            continue
        if not APP_ID_RE.fullmatch(app_id):
            continue
        if installation.casefold() == "user":
            user_apps.add(app_id)
        else:
            system_apps.add(app_id)
    return user_apps, system_apps
