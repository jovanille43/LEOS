"""Create user-scoped, theme-aware LEOS branding assets.

Official files under /usr/share/leos/branding are never modified. A linear RGB
matrix maps the original cyan/magenta endpoints to the user's A/B pair while
preserving the neutral axis, so metallic greys and white highlights remain
neutral. JPEGs, SVG color stops and intro videos use the same transform.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from desktop.themes import DEFAULT_COLOR_A, DEFAULT_COLOR_B, normalize_color


_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
_IMAGE_NAMES = {
    "desktop_logo": "desktop-logo.jpeg",
    "gaming_logo": "gaming-logo.jpeg",
}
_WALLPAPER_NAMES = {
    "desktop_wallpaper": ("desktop-leos.svg", "desktop-logo.jpeg"),
    "gaming_wallpaper": ("gaming-leos.svg", "gaming-logo.jpeg"),
}
_VIDEO_NAMES = {
    "desktop_intro": "desktop-intro.mov",
    "gaming_intro": "gaming-intro.mp4",
}


def _rgb01(hex_color: str) -> tuple[float, float, float]:
    color = normalize_color(hex_color)
    return tuple(int(color[index:index + 2], 16) / 255.0 for index in (1, 3, 5))


def _inverse_3x3(matrix: tuple[tuple[float, float, float], ...]) -> tuple[tuple[float, float, float], ...]:
    """Invert a 3x3 matrix using pivoted Gaussian elimination."""
    rows = [
        [float(matrix[row][col]) for col in range(3)]
        + [1.0 if row == col else 0.0 for col in range(3)]
        for row in range(3)
    ]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(rows[row][column]))
        if abs(rows[pivot][column]) < 1e-10:
            raise ValueError("The original LEOS gradient colors do not form an invertible transform")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(3):
            if row == column:
                continue
            factor = rows[row][column]
            rows[row] = [
                rows[row][index] - factor * rows[column][index]
                for index in range(6)
            ]
    return tuple(tuple(rows[row][col + 3] for col in range(3)) for row in range(3))


def build_color_matrix(
    color_a: str,
    color_b: str,
    source_a: str = DEFAULT_COLOR_A,
    source_b: str = DEFAULT_COLOR_B,
) -> tuple[tuple[float, float, float], ...]:
    """Map old A/B gradient endpoints to new A/B while preserving neutral grey."""
    old_a = _rgb01(source_a)
    old_b = _rgb01(source_b)
    new_a = _rgb01(color_a)
    new_b = _rgb01(color_b)

    # Columns are source A, source B and neutral white. The neutral constraint
    # keeps the silver lion, white highlights and grey details colour-neutral.
    source = (
        (old_a[0], old_b[0], 1.0),
        (old_a[1], old_b[1], 1.0),
        (old_a[2], old_b[2], 1.0),
    )
    target = (
        (new_a[0], new_b[0], 1.0),
        (new_a[1], new_b[1], 1.0),
        (new_a[2], new_b[2], 1.0),
    )
    inverse = _inverse_3x3(source)
    return tuple(
        tuple(
            sum(target[row][inner] * inverse[inner][col] for inner in range(3))
            for col in range(3)
        )
        for row in range(3)
    )


def transform_rgb(
    rgb: tuple[float, float, float],
    matrix: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    """Apply a 3x3 normalized RGB transform with channel clamping."""
    return tuple(
        min(1.0, max(0.0, sum(matrix[row][col] * rgb[col] for col in range(3))))
        for row in range(3)
    )


def _cache_root() -> Path:
    configured = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(configured).expanduser() if configured and Path(configured).is_absolute() else Path.home() / ".cache"
    return base / "leos" / "theme-assets"


def _branding_root() -> Path:
    return Path(__file__).resolve().parents[1] / "branding"


def _safe_cache_directory(path: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise OSError("LEOS theme asset cache cannot contain symbolic links")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    if path.is_symlink() or not path.is_dir():
        raise OSError("LEOS theme asset cache is not a regular directory")


def _image_transform(source: Path, destination: Path, matrix) -> bool:
    """Recolour a logo into a PNG variant without editing the JPEG source."""
    from PySide6.QtGui import QColor, QImage

    if source.is_symlink() or not source.is_file():
        return False
    image = QImage(str(source))
    if image.isNull():
        return False
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            red, green, blue = transform_rgb(
                (pixel.redF(), pixel.greenF(), pixel.blueF()), matrix
            )
            image.setPixelColor(
                x,
                y,
                QColor.fromRgbF(red, green, blue, pixel.alphaF()),
            )

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".png", dir=destination.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        if not image.save(str(temporary), "PNG"):
            return False
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination.is_file() and destination.stat().st_size > 0


def _transform_svg(
    source: Path,
    destination: Path,
    matrix,
    emblem: Path | None,
) -> bool:
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 2 * 1024 * 1024:
        return False
    content = source.read_text(encoding="utf-8")
    if emblem is not None:
        # Keep the SVG linked to a generated user-scoped emblem variant.
        old_name = "desktop-logo.jpeg" if "desktop" in source.name else "gaming-logo.jpeg"
        content = content.replace(f"../{old_name}", emblem.resolve().as_uri())

    def recolor(match: re.Match[str]) -> str:
        value = _rgb01(match.group(0))
        mapped = transform_rgb(value, matrix)
        channels = tuple(max(0, min(255, round(channel * 255))) for channel in mapped)
        return "#{:02X}{:02X}{:02X}".format(*channels)

    content = _HEX_COLOR_RE.sub(recolor, content)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=".svg", dir=destination.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(content, encoding="utf-8")
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination.is_file() and destination.stat().st_size > 0


def _transform_video(source: Path, destination: Path, matrix) -> bool:
    """Re-encode one intro with the exact same RGB endpoint transform and copied audio."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or source.is_symlink() or not source.is_file():
        return False

    keys = ("rr", "rg", "rb", "gr", "gg", "gb", "br", "bg", "bb")
    values = [matrix[row][col] for row in range(3) for col in range(3)]
    color_filter = "colorchannelmixer=" + ":".join(
        f"{key}={value:.8f}" for key, value in zip(keys, values)
    )
    temporary = destination.with_name(destination.stem + ".tmp" + destination.suffix)
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source),
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", color_filter + ",format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "copy", "-map_metadata", "0",
        str(temporary),
    ]
    try:
        result = subprocess.run(
            command, shell=False, capture_output=True, text=True,
            timeout=180, check=False,
        )
        if result.returncode != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
            return False
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    except (OSError, subprocess.TimeoutExpired):
        return False
    finally:
        temporary.unlink(missing_ok=True)
    return destination.is_file() and destination.stat().st_size > 0


def source_asset_urls(branding_root: Path | None = None) -> dict[str, str]:
    """Return original source file URLs for graceful fallback."""
    root = branding_root or _branding_root()
    return {
        "desktopLogoUrl": (root / "desktop-logo.jpeg").as_uri(),
        "gamingLogoUrl": (root / "gaming-logo.jpeg").as_uri(),
        "desktopWallpaperUrl": (root / "wallpapers" / "desktop-leos.svg").as_uri(),
        "gamingWallpaperUrl": (root / "wallpapers" / "gaming-leos.svg").as_uri(),
        "desktopIntroUrl": (root / "animations" / "desktop-intro.mov").as_uri(),
        "gamingIntroUrl": (root / "animations" / "gaming-intro.mp4").as_uri(),
    }


def build_themed_branding_assets(
    color_a: str,
    color_b: str,
    branding_root: Path | None = None,
) -> dict[str, str]:
    """Build or reuse themed branding assets in a private cache directory."""
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    root = branding_root or _branding_root()
    original_urls = source_asset_urls(root)
    pair_id = hashlib.sha256(f"{first}|{second}".encode("ascii")).hexdigest()[:20]
    cache = _cache_root() / pair_id
    _safe_cache_directory(cache)

    lock_path = cache / ".build.lock"
    if lock_path.is_symlink():
        raise OSError("LEOS theme asset lock cannot be a symbolic link")

    matrix = build_color_matrix(first, second)
    with lock_path.open("a", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            assets: dict[str, str] = {}
            logo_paths: dict[str, Path] = {}
            for key, filename in _IMAGE_NAMES.items():
                output = cache / (Path(filename).stem + ".png")
                source = root / filename
                if output.is_symlink():
                    raise OSError("LEOS theme logo cache cannot contain symbolic links")
                if not output.is_file() or output.stat().st_size == 0:
                    _image_transform(source, output, matrix)
                asset_key = "desktopLogoUrl" if key == "desktop_logo" else "gamingLogoUrl"
                if output.is_file() and not output.is_symlink() and output.stat().st_size > 0:
                    logo_paths[key] = output
                    assets[asset_key] = output.as_uri()
                else:
                    logo_paths[key] = source
                    assets[asset_key] = original_urls[asset_key]

            for key, (filename, emblem_name) in _WALLPAPER_NAMES.items():
                output = cache / filename
                source = root / "wallpapers" / filename
                if output.is_symlink():
                    raise OSError("LEOS theme wallpaper cache cannot contain symbolic links")
                emblem_key = "desktop_logo" if key == "desktop_wallpaper" else "gaming_logo"
                if not output.is_file() or output.stat().st_size == 0:
                    _transform_svg(source, output, matrix, logo_paths[emblem_key])
                assets["desktopWallpaperUrl" if key == "desktop_wallpaper" else "gamingWallpaperUrl"] = (
                    output.as_uri() if output.is_file() and not output.is_symlink()
                    else original_urls["desktopWallpaperUrl" if key == "desktop_wallpaper" else "gamingWallpaperUrl"]
                )

            for key, filename in _VIDEO_NAMES.items():
                output = cache / filename
                source = root / "animations" / filename
                if output.is_symlink():
                    raise OSError("LEOS theme video cache cannot contain symbolic links")
                if not output.is_file() or output.stat().st_size == 0:
                    _transform_video(source, output, matrix)
                assets["desktopIntroUrl" if key == "desktop_intro" else "gamingIntroUrl"] = (
                    output.as_uri() if output.is_file() and not output.is_symlink()
                    else original_urls["desktopIntroUrl" if key == "desktop_intro" else "gamingIntroUrl"]
                )
            return assets
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
