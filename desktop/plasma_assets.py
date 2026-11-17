"""Generate user-scoped A/B variants of LEOS Plasma and Aurorae SVG assets.

Packaged SVGs remain the immutable source of truth. The generated copies keep
all paths, geometry, sizing and state IDs intact while replacing only the
known LEOS accent-color families with the currently selected A/B pair.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from desktop.themes import normalize_hex_color, palette_for_settings
from leos_core.paths import data_home as xdg_data_home

COLOR_LITERAL = re.compile(r"#[0-9a-fA-F]{6}\b")
SVG_NAMESPACE = "http://www.w3.org/2000/svg"

# The original artwork uses several light, dark and blended shades for each
# accent. These semantic groups preserve the design's hierarchy after A/B
# substitution rather than flattening every occurrence to one solid color.
_PRIMARY_LIGHT = ("#67DFF8", "#6BE6FF", "#5EDFFF", "#65E5FF")
_PRIMARY_DARK = ("#2C6D91", "#17313D", "#183440", "#0E3442", "#1B4262")
_SECONDARY_LIGHT = ("#E66BD5", "#EF70D9", "#F078D7")
_SECONDARY_DARK = ("#8B3A83",)
_BLEND = ("#899BFF", "#A28CFF", "#83BFFF")


def _rgb(color: str) -> tuple[int, int, int]:
    normalized = normalize_hex_color(color)
    if normalized is None:
        raise ValueError("Invalid LEOS accent color")
    return tuple(int(normalized[index:index + 2], 16) for index in (1, 3, 5))


def _hex(channels: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, value)):02X}" for value in channels)


def _mix(first: str, second: str, ratio: float) -> str:
    a, b = _rgb(first), _rgb(second)
    return _hex(tuple(round(x * (1 - ratio) + y * ratio) for x, y in zip(a, b)))


def _shade(color: str, factor: float) -> str:
    return _hex(tuple(round(channel * factor) for channel in _rgb(color)))


def _lighten(color: str, ratio: float) -> str:
    return _mix(color, "#FFFFFF", ratio)


def accent_color_map(accent_a: str, accent_b: str) -> dict[str, str]:
    """Return an explicit, case-insensitive map for every branded SVG shade."""
    a = normalize_hex_color(accent_a)
    b = normalize_hex_color(accent_b)
    if a is None or b is None:
        raise ValueError("LEOS A/B theme accents are invalid")

    mapping = {
        "#00D9FF": a,
        "#E33BFF": b,
    }
    for color in _PRIMARY_LIGHT:
        mapping[color] = _lighten(a, 0.20)
    for color in _PRIMARY_DARK:
        mapping[color] = _shade(a, 0.46)
    for color in _SECONDARY_LIGHT:
        mapping[color] = _lighten(b, 0.20)
    for color in _SECONDARY_DARK:
        mapping[color] = _shade(b, 0.46)
    middle = _mix(a, b, 0.5)
    for color in _BLEND:
        mapping[color] = _lighten(middle, 0.12)
    return {source.lower(): target for source, target in mapping.items()}


def _recolor_svg(payload: bytes, color_map: dict[str, str], source: Path) -> bytes:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError(f"LEOS SVG resource is invalid: {source}") from exc

    for element in root.iter():
        for name, value in tuple(element.attrib.items()):
            # Hex replacements cover fill/stroke/stop-color and inline CSS
            # declarations while preserving url(#gradient) references.
            if name.lower() in {
                "fill", "stroke", "stop-color", "style", "color",
                "flood-color", "lighting-color",
            }:
                element.set(
                    name,
                    COLOR_LITERAL.sub(
                        lambda match: color_map.get(match.group(0).lower(), match.group(0)),
                        value,
                    ),
                )

        if element.text:
            element.text = element.text.replace(
                "cyan → blue-violet → magenta", "A → transition → B"
            ).replace(
                "cyan-violet-magenta", "A/B"
            ).replace(
                "cyan to magenta", "A to B"
            )

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _metadata_payload(path: Path, payload: bytes) -> bytes:
    if path.name == "metadata.json":
        try:
            document = json.loads(payload.decode("utf-8"))
            plugin = document["KPlugin"]
            if not isinstance(plugin, dict) or plugin.get("Id") != "leos":
                raise ValueError("LEOS Plasma metadata has an unexpected plugin ID")
            plugin["Description"] = (
                "Dark LEOS Plasma surfaces with the selected A/B accent colors."
            )
            return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"LEOS metadata is invalid: {path}") from exc

    if path.name == "metadata.desktop":
        try:
            text = payload.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError(f"LEOS Aurorae metadata is invalid: {path}") from exc
        text = re.sub(
            r"(?m)^Comment=.*$",
            "Comment=LEOS window decoration using the selected A/B accent colors",
            text,
        )
        return text.encode("utf-8")
    return payload


def _atomic_write(path: Path, payload: bytes) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise OSError(f"Refusing to overwrite a symbolic link: {path}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _prepare_directory(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise OSError(f"LEOS theme output directory cannot be a symbolic link: {path}")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise OSError(f"LEOS theme output directory cannot be a symbolic link: {path}")
    os.chmod(path, 0o700)


def _generate_tree(source: Path, destination: Path, color_map: dict[str, str]) -> None:
    if source.is_symlink() or not source.is_dir():
        raise FileNotFoundError(f"LEOS theme source directory is missing: {source}")
    _prepare_directory(destination)

    files = sorted(source.rglob("*"))
    if not files:
        raise ValueError(f"LEOS theme source directory is empty: {source}")

    for source_file in files:
        if source_file.is_symlink():
            raise OSError(f"Symbolic links are not accepted in LEOS theme assets: {source_file}")
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if target.parent.is_symlink():
            raise OSError(f"Symbolic-link LEOS theme path rejected: {target.parent}")
        payload = source_file.read_bytes()
        if source_file.suffix.lower() == ".svg":
            payload = _recolor_svg(payload, color_map, source_file)
        else:
            payload = _metadata_payload(source_file, payload)
        _atomic_write(target, payload)


def generate_user_theme_assets(
    settings: Any,
    data_root: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, str]:
    """Generate matching Plasma Style and Aurorae assets in the user's XDG data."""
    root = Path(data_root) if data_root is not None else xdg_data_home()
    package_root = Path(source_root) if source_root is not None else Path(__file__).resolve().parents[1]
    palette = palette_for_settings(settings)
    accent_a = normalize_hex_color(palette.get("accent_primary"))
    accent_b = normalize_hex_color(palette.get("accent_secondary"))
    if accent_a is None or accent_b is None:
        raise ValueError("LEOS A/B theme accents are invalid")
    color_map = accent_color_map(accent_a, accent_b)

    for base in (root / "plasma", root / "aurorae"):
        if base.is_symlink():
            raise OSError(f"LEOS theme data root cannot be a symbolic link: {base}")

    plasma_destination = root / "plasma" / "desktoptheme" / "leos"
    aurorae_destination = root / "aurorae" / "themes" / "leos"
    _generate_tree(package_root / "plasma-theme" / "leos", plasma_destination, color_map)
    _generate_tree(package_root / "aurorae" / "leos", aurorae_destination, color_map)
    return {
        "plasma": str(plasma_destination),
        "aurorae": str(aurorae_destination),
        "accent_primary": accent_a,
        "accent_secondary": accent_b,
    }
