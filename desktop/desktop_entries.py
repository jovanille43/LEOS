"""Pure helpers for freedesktop Desktop Entry visibility and localization."""

from __future__ import annotations


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
