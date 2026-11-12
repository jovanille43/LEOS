"""Pure helpers for freedesktop Desktop Entry visibility and localization."""

from __future__ import annotations

import os
from pathlib import Path

from leos_core.paths import data_home as xdg_data_home
from leos_core.text import normalize_search_text


def desktop_application_dirs() -> tuple[Path, ...]:
    """Return low-to-high priority directories for the menu's last-wins merge.

    XDG_DATA_HOME has highest precedence. XDG_DATA_DIRS is ordered from
    highest to lowest precedence, so it is reversed for this caller.
    """
    configured = os.environ.get("XDG_DATA_DIRS", "").strip()
    roots = configured.split(os.pathsep) if configured else ["/usr/local/share", "/usr/share"]
    system_dirs: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        candidate = Path(root.strip()).expanduser()
        if not root.strip() or not candidate.is_absolute():
            continue
        application_dir = candidate / "applications"
        if application_dir not in seen:
            system_dirs.append(application_dir)
            seen.add(application_dir)

    user_dir = xdg_data_home() / "applications"
    directories = [directory for directory in reversed(system_dirs) if directory != user_dir]
    directories.append(user_dir)
    return tuple(directories)


def localized_desktop_value(
    values: dict[str, str], key: str, locale_name: str
) -> str:
    """Choose a locale-specific Desktop Entry value before its generic fallback."""
    locale = str(locale_name or "").replace("-", "_")
    candidates: list[str] = []
    if locale and locale.casefold() != "c":
        candidates.append(f"{key}[{locale}]")
        language = locale.split("_", 1)[0]
        if language and language != locale:
            candidates.append(f"{key}[{language}]")
    for candidate in candidates:
        value = values.get(candidate, "").strip()
        if value:
            return value
    return values.get(key, "").strip()


def desktop_entry_is_visible(
    values: dict[str, str],
    current_desktops: set[str],
) -> bool:
    """Apply Hidden, NoDisplay, OnlyShowIn and NotShowIn visibility rules."""
    if values.get("Hidden", "").casefold() == "true":
        return False
    if values.get("NoDisplay", "").casefold() == "true":
        return False
    only_show_in = {
        item.strip().casefold()
        for item in values.get("OnlyShowIn", "").split(";")
        if item.strip()
    }
    not_show_in = {
        item.strip().casefold()
        for item in values.get("NotShowIn", "").split(";")
        if item.strip()
    }
    desktops = {item.strip().casefold() for item in current_desktops if item.strip()}
    if only_show_in and not (only_show_in & desktops):
        return False
    if not_show_in & desktops:
        return False
    return True


def filter_desktop_applications(
    items: list[dict[str, str]],
    category: str,
    favourites: list[str],
    search_query: str = "",
    recently_used: list[str] | None = None,
) -> list[dict[str, str]]:
    """Filter application entries and preserve saved order in the Favourites view."""
    query = normalize_search_text(search_query)
    pinned_order = list(favourites)
    pinned_ids = set(pinned_order)
    recent_order = list(recently_used or [])
    recent_ids = set(recent_order)
    selected: list[dict[str, str]] = []
    for item in items:
        desktop_id = str(item.get("desktopId", ""))
        item_category = str(item.get("category", ""))
        if category == "Favoris":
            if desktop_id not in pinned_ids:
                continue
        elif category == "Récemment utilisées":
            if desktop_id not in recent_ids:
                continue
        elif category != "Tout" and item_category != category:
            continue

        haystack = normalize_search_text(" ".join((
            str(item.get("name", "")),
            desktop_id,
            str(item.get("description", "")),
            item_category,
        )))
        if query and query not in haystack:
            continue
        selected.append(item)

    if category == "Favoris":
        selected.sort(key=lambda item: pinned_order.index(str(item.get("desktopId", ""))))
    elif category == "Récemment utilisées":
        selected.sort(key=lambda item: recent_order.index(str(item.get("desktopId", ""))))
    return selected
