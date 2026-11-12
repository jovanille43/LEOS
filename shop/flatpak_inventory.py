"""Parse the human-readable Flatpak application inventory safely."""

from __future__ import annotations

import re
from urllib.parse import urlsplit


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



def trusted_flathub_remote_url(output: str) -> str:
    """Return the configured canonical Flathub URL, or an empty string."""
    for line in output.splitlines():
        columns = line.split()
        if len(columns) < 2 or columns[0].casefold() != "flathub":
            continue
        try:
            parsed = urlsplit(columns[1])
            host = (parsed.hostname or "").casefold()
            valid_host = host in {"dl.flathub.org", "flathub.org"}
            valid_path = parsed.path.rstrip("/") in {"/repo", "/repo/flathub.flatpakrepo"}
            no_credentials = parsed.username is None and parsed.password is None
            no_port = parsed.port is None
            if (
                parsed.scheme == "https"
                and valid_host
                and valid_path
                and no_credentials
                and no_port
                and not parsed.query
                and not parsed.fragment
            ):
                return columns[1]
        except ValueError:
            continue
    return ""


def is_trusted_flathub_remote(output: str) -> bool:
    """Accept only a Flathub remote with a canonical HTTPS repository URL."""
    return bool(trusted_flathub_remote_url(output))
