"""Generate user-scoped LEOS wallpapers using the active A/B theme accents."""

from __future__ import annotations

import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from leos_core.paths import data_home
from desktop.themes import normalize_hex_color, palette_for_settings

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"

WALLPAPER_FILES = {
    "desktop": ("desktop-leos.svg", "desktop-logo-alpha.png"),
    "gaming": ("gaming-leos.svg", "gaming-logo-alpha.png"),
}


def _rgb(value: str) -> tuple[int, int, int]:
    normalized = normalize_hex_color(value)
    if normalized is None:
        raise ValueError("Invalid LEOS accent color")
    return tuple(int(normalized[index:index + 2], 16) for index in (1, 3, 5))


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, channel)):02X}" for channel in rgb)


def _shade(color: str, factor: float) -> str:
    return _hex(tuple(round(channel * factor) for channel in _rgb(color)))


def _mix(first: str, second: str, ratio: float) -> str:
    a = _rgb(first)
    b = _rgb(second)
    return _hex(tuple(round(x * (1.0 - ratio) + y * ratio) for x, y in zip(a, b)))


def _color_map(accent_a: str, accent_b: str, kind: str) -> dict[str, str]:
    midpoint = _mix(accent_a, accent_b, 0.5)
    mapping = {
        "#00d9ff": accent_a,
        "#00cfff": accent_a,
        "#00b9e8": accent_a,
        "#006782": _shade(accent_a, 0.45),
        "#006b8a": _shade(accent_a, 0.45),
        "#087b9a": _shade(accent_a, 0.50),
        "#e33bff": accent_b,
        "#d32ce8": accent_b,
        "#67136f": _shade(accent_b, 0.45),
        "#761286": _shade(accent_b, 0.45),
        "#a12eae": _shade(accent_b, 0.50),
        "#8c6eaa": midpoint,
    }
    # Dark, fully transparent end-stops remain close to the original neutral
    # background; only the visible glow colors move with the selected accents.
    if kind not in WALLPAPER_FILES:
        raise ValueError("Unknown LEOS wallpaper kind")
    return mapping


def _atomic_write(path: Path, payload: bytes, mode: int = 0o600) -> None:
    if path.is_symlink():
        raise OSError("Refusing to replace a symbolic link in LEOS wallpaper output")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _serialize_wallpaper(source: Path, kind: str, accent_a: str, accent_b: str) -> bytes:
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"LEOS wallpaper source is missing: {source}")

    ET.register_namespace("", SVG_NAMESPACE)
    ET.register_namespace("xlink", XLINK_NAMESPACE)
    root = ET.parse(source).getroot()
    color_map = _color_map(accent_a, accent_b, kind)

    def recolor(value: str) -> str:
        return color_map.get(value.lower(), value)

    for element in root.iter():
        for attribute, value in tuple(element.attrib.items()):
            if attribute.lower() in {"stop-color", "stroke", "fill"}:
                element.set(attribute, recolor(value))
        if element.text:
            text = element.text.replace("halos cyan et magenta", "halos A/B personnalisés")
            text = text.replace("arcs cyan et magenta", "arcs A/B personnalisés")
            text = text.replace("cyan et magenta", "A et B")
            element.text = text

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def generate_user_wallpapers(
    settings: Any,
    destination: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, str]:
    """Create custom Desktop/Gaming SVG copies without modifying packaged originals.

    The copied transparent emblems are placed one directory above the wallpaper
    files so the original relative SVG image references continue to resolve.
    """
    package_root = source_root or Path(__file__).resolve().parents[1] / "branding"
    source_wallpapers = package_root / "wallpapers"
    output_dir = destination or data_home() / "leos" / "wallpapers"

    if output_dir.is_symlink() or output_dir.parent.is_symlink():
        raise OSError("LEOS wallpaper output directory cannot be a symbolic link")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir.parent, 0o700)
    os.chmod(output_dir, 0o700)

    palette = palette_for_settings(settings)
    accent_a = normalize_hex_color(palette.get("accent_primary"))
    accent_b = normalize_hex_color(palette.get("accent_secondary"))
    if accent_a is None or accent_b is None:
        raise ValueError("LEOS A/B theme accents are invalid")

    # The packaged source of truth remains untouched. Store logo copies beside
    # the generated wallpaper directory to preserve ../<logo>.png in the SVG.
    asset_directory = output_dir.parent
    results: dict[str, str] = {}
    for kind, (filename, logo_filename) in WALLPAPER_FILES.items():
        source_logo = package_root / logo_filename
        if source_logo.is_symlink() or not source_logo.is_file():
            raise FileNotFoundError(f"LEOS transparent emblem is missing: {source_logo}")
        target_logo = asset_directory / logo_filename
        if target_logo.is_symlink():
            raise OSError("Refusing to overwrite a symbolic-link LEOS emblem")
        _atomic_write(target_logo, source_logo.read_bytes())

        source_svg = source_wallpapers / filename
        payload = _serialize_wallpaper(source_svg, kind, accent_a, accent_b)
        target_svg = output_dir / filename
        _atomic_write(target_svg, payload)
        results[kind] = str(target_svg)

    return results
