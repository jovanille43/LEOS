"""Generate user-scoped LEOS artwork variants from the official brand assets.

Only saturated pixels close to the two historical accent hues are shifted.
Alpha, brightness, saturation, neutral metallic details and geometry are kept.
The packaged PNG/SVG source files are never modified.
"""

from __future__ import annotations

import colorsys
import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Mapping

from desktop.themes import THEME_PALETTES, palette_for_theme

_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
_SOURCE_PRIMARY_HUE = 190.0 / 360.0
_SOURCE_SECONDARY_HUE = 292.0 / 360.0
_MAX_SVG_BYTES = 4 * 1024 * 1024
_MAX_IMAGE_PIXELS = 18_000_000


def _valid_hex(value: str) -> bool:
    return isinstance(value, str) and _HEX_COLOR.fullmatch(value) is not None


def _hue_distance(first: float, second: float) -> float:
    distance = abs(first - second) % 1.0
    return min(distance, 1.0 - distance)


def recolor_hex_color(
    source: str,
    accent_primary: str,
    accent_secondary: str,
) -> str:
    """Shift cyan-like pixels to primary and magenta-like pixels to secondary.

    Hue is changed only for saturated, visibly colored pixels close to one of
    the two source accent families. Saturation and value remain unchanged so
    glow intensity, antialiasing and metallic luminance gradients are retained.
    """
    if not all(_valid_hex(value) for value in (source, accent_primary, accent_secondary)):
        raise ValueError("Theme asset colors must be six-digit hexadecimal values")

    rgb = tuple(int(source[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
    if saturation < 0.16 or value < 0.14:
        return source.lower()

    primary_distance = _hue_distance(hue, _SOURCE_PRIMARY_HUE)
    secondary_distance = _hue_distance(hue, _SOURCE_SECONDARY_HUE)
    distance, target = (
        (primary_distance, accent_primary)
        if primary_distance <= secondary_distance
        else (secondary_distance, accent_secondary)
    )
    if distance > 58.0 / 360.0:
        return source.lower()

    target_rgb = tuple(
        int(target[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    target_hue = colorsys.rgb_to_hsv(*target_rgb)[0]
    red, green, blue = colorsys.hsv_to_rgb(target_hue, saturation, value)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255), round(green * 255), round(blue * 255)
    )


def recolor_svg_markup(
    markup: str,
    accent_primary: str,
    accent_secondary: str,
) -> str:
    """Recolor SVG hex paint values while leaving neutrals and SVG structure intact."""
    if not isinstance(markup, str) or len(markup.encode("utf-8")) > _MAX_SVG_BYTES:
        raise ValueError("SVG source is invalid or exceeds its size limit")
    if not _valid_hex(accent_primary) or not _valid_hex(accent_secondary):
        raise ValueError("Theme accent colors must be six-digit hexadecimal values")
    return _HEX_COLOR.sub(
        lambda match: recolor_hex_color(
            match.group(0), accent_primary, accent_secondary
        ),
        markup,
    )


def _safe_output_directory(path: Path) -> None:
    path = path.expanduser()
    if path.exists() and path.is_symlink():
        raise ValueError("Theme asset output directory cannot be a symbolic link")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("Theme asset output path is not a safe directory")
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def render_svg_theme(
    source_path: Path,
    output_path: Path,
    palette: Mapping[str, str],
    emblem_path: Path | None = None,
) -> Path:
    """Write a recolored SVG copy; optionally relink its official emblem copy."""
    source_path = Path(source_path)
    output_path = Path(output_path)
    if source_path.is_symlink() or not source_path.is_file():
        raise FileNotFoundError("Official LEOS SVG source is not a regular file")
    raw = source_path.read_bytes()
    if len(raw) > _MAX_SVG_BYTES:
        raise ValueError("Official LEOS SVG exceeds the allowed size")
    markup = raw.decode("utf-8")
    rendered = recolor_svg_markup(
        markup,
        palette["accent_primary"],
        palette["accent_secondary"],
    )
    if emblem_path is not None:
        emblem_uri = Path(emblem_path).resolve().as_uri()
        rendered = rendered.replace("../desktop-logo-alpha.png", emblem_uri)
        rendered = rendered.replace("../gaming-logo-alpha.png", emblem_uri)

    _safe_output_directory(output_path.parent)
    if output_path.is_symlink():
        raise ValueError("Theme asset output file cannot be a symbolic link")
    fd, temporary = tempfile.mkstemp(
        prefix="leos-svg-", suffix=".tmp", dir=output_path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, output_path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return output_path


def render_logo_theme(
    source_path: Path,
    output_path: Path,
    palette: Mapping[str, str],
) -> Path:
    """Recolor a transparent official emblem using Qt's already-packaged QImage."""
    from PySide6.QtGui import QColor, QImage

    source_path = Path(source_path)
    output_path = Path(output_path)
    if source_path.is_symlink() or not source_path.is_file():
        raise FileNotFoundError("Official LEOS emblem source is not a regular file")
    image = QImage(str(source_path))
    if image.isNull():
        raise ValueError("Official LEOS emblem could not be decoded")
    if image.width() * image.height() > _MAX_IMAGE_PIXELS:
        raise ValueError("Official LEOS emblem exceeds the pixel limit")

    image = image.convertToFormat(QImage.Format_ARGB32)
    primary = palette["accent_primary"]
    secondary = palette["accent_secondary"]
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            if pixel.alpha() == 0:
                continue
            recolored = recolor_hex_color(pixel.name(), primary, secondary)
            if recolored != pixel.name().lower():
                replacement = QColor(recolored)
                replacement.setAlpha(pixel.alpha())
                image.setPixelColor(x, y, replacement)

    _safe_output_directory(output_path.parent)
    if output_path.is_symlink():
        raise ValueError("Theme asset output file cannot be a symbolic link")
    fd, temporary = tempfile.mkstemp(
        prefix="leos-logo-", suffix=".png", dir=output_path.parent
    )
    os.close(fd)
    try:
        if not image.save(temporary, "PNG"):
            raise OSError("Qt could not encode the recolored LEOS emblem")
        os.chmod(temporary, 0o600)
        os.replace(temporary, output_path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return output_path


class ThemeAssetManager:
    """Create cached logo and wallpaper copies without touching packaged assets."""

    def __init__(
        self,
        branding_dir: Path | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self.branding_dir = branding_dir or Path(__file__).resolve().parents[1] / "branding"
        if cache_dir is None:
            configured = Path(os.environ.get("XDG_CACHE_HOME", "")).expanduser()
            cache_dir = (
                configured
                if str(configured) and configured.is_absolute()
                else Path.home() / ".cache"
            )
        self.cache_dir = Path(cache_dir)

    def paths_for_theme(self, theme: str) -> dict[str, str]:
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        fingerprint = hashlib.sha256(
            (theme + palette["accent_primary"] + palette["accent_secondary"]).encode("ascii")
        ).hexdigest()[:16]
        output_dir = self.cache_dir / "leos" / "themes" / fingerprint
        _safe_output_directory(output_dir)

        desktop_logo_source = self.branding_dir / "desktop-logo-alpha.png"
        gaming_logo_source = self.branding_dir / "gaming-logo-alpha.png"
        desktop_logo = output_dir / "desktop-logo.png"
        gaming_logo = output_dir / "gaming-logo.png"
        desktop_wallpaper = output_dir / "desktop-wallpaper.svg"
        gaming_wallpaper = output_dir / "gaming-wallpaper.svg"

        if not desktop_logo.is_file():
            render_logo_theme(desktop_logo_source, desktop_logo, palette)
        if not gaming_logo.is_file():
            render_logo_theme(gaming_logo_source, gaming_logo, palette)
        if not desktop_wallpaper.is_file():
            render_svg_theme(
                self.branding_dir / "wallpapers" / "desktop-leos.svg",
                desktop_wallpaper,
                palette,
                desktop_logo,
            )
        if not gaming_wallpaper.is_file():
            render_svg_theme(
                self.branding_dir / "wallpapers" / "gaming-leos.svg",
                gaming_wallpaper,
                palette,
                gaming_logo,
            )

        return {
            "desktop_logo": desktop_logo.as_uri(),
            "gaming_logo": gaming_logo.as_uri(),
            "desktop_wallpaper": desktop_wallpaper.as_uri(),
            "gaming_wallpaper": gaming_wallpaper.as_uri(),
        }
