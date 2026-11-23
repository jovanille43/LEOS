"""Create user-scoped, theme-aware LEOS branding assets.

Official files under /usr/share/leos/branding are never modified. A linear RGB
matrix maps the original cyan/magenta endpoints to the user's A/B pair while
preserving the neutral axis, so metallic greys and white highlights remain
neutral. JPEGs, SVG color stops and intro videos use the same transform.
"""

from __future__ import annotations

import fcntl
import hashlib
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from desktop.themes import SOURCE_COLOR_A, SOURCE_COLOR_B, normalize_color


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
    source_a: str = SOURCE_COLOR_A,
    source_b: str = SOURCE_COLOR_B,
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


def _remove_dark_edge_matte(image) -> bool:
    """Make a JPEG's connected near-black edge background transparent.

    Only dark pixels connected to the image border are removed. This preserves
    enclosed black details in the lion and avoids a global black-colour key.
    """
    width, height = image.width(), image.height()
    if width < 3 or height < 3:
        return False

    corners = [
        image.pixelColor(0, 0), image.pixelColor(width - 1, 0),
        image.pixelColor(0, height - 1), image.pixelColor(width - 1, height - 1),
    ]
    dark_corners = [
        (pixel.red(), pixel.green(), pixel.blue())
        for pixel in corners
        if max(pixel.red(), pixel.green(), pixel.blue()) <= 96
    ]
    if len(dark_corners) < 3:
        return False

    background = tuple(
        sorted(channel)[len(channel) // 2]
        for channel in zip(*dark_corners)
    )
    total = width * height
    # 0 = unseen, 1 = queued, 2 = connected matte, 3 = non-matte boundary.
    state = bytearray(total)
    pending: list[int] = []

    def enqueue(index: int) -> None:
        if state[index] == 0:
            state[index] = 1
            pending.append(index)

    for x in range(width):
        enqueue(x)
        enqueue((height - 1) * width + x)
    for y in range(height):
        enqueue(y * width)
        enqueue(y * width + width - 1)

    while pending:
        index = pending.pop()
        x = index % width
        pixel = image.pixelColor(x, index // width)
        rgb = (pixel.red(), pixel.green(), pixel.blue())
        distance = math.sqrt(sum(
            (rgb[channel] - background[channel]) ** 2
            for channel in range(3)
        ))
        # The edge matte is expected to be almost black. A conservative
        # distance and brightness bound prevents the lion itself being keyed.
        if max(rgb) > 108 or distance > 78:
            state[index] = 3
            continue
        state[index] = 2
        if x > 0:
            enqueue(index - 1)
        if x + 1 < width:
            enqueue(index + 1)
        if index >= width:
            enqueue(index - width)
        if index + width < total:
            enqueue(index + width)

    removed = False
    for index, status in enumerate(state):
        if status != 2:
            continue
        pixel = image.pixelColor(index % width, index // width)
        rgb = (pixel.red(), pixel.green(), pixel.blue())
        distance = math.sqrt(sum(
            (rgb[channel] - background[channel]) ** 2
            for channel in range(3)
        ))
        # Feather the outer edge to avoid a harsh cut around antialiased
        # artwork; pixels matching the black matte become fully transparent.
        alpha = max(0, min(255, round((distance - 24.0) * 255.0 / 54.0)))
        pixel.setAlpha(alpha)
        image.setPixelColor(index % width, index // width, pixel)
        removed = True
    return removed


def _crop_transparent_bounds(image):
    """Trim the fully transparent outer canvas while preserving a small halo."""
    width, height = image.width(), image.height()
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if image.pixelColor(x, y).alpha() > 48:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    if right < left or bottom < top:
        return image
    content_width, content_height = right - left + 1, bottom - top + 1
    padding = max(6, round(max(content_width, content_height) * 0.025))
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(width - 1, right + padding)
    bottom = min(height - 1, bottom + padding)
    return image.copy(left, top, right - left + 1, bottom - top + 1)


def _image_transform(source: Path, destination: Path, matrix) -> bool:
    """Recolour a logo into a cropped, transparent PNG without editing its JPEG."""
    from PySide6.QtGui import QColor, QImage

    if source.is_symlink() or not source.is_file():
        return False
    image = QImage(str(source))
    if image.isNull():
        return False
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    _remove_dark_edge_matte(image)
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

    image = _crop_transparent_bounds(image)

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


def _available_video_encoder(ffmpeg: str) -> str | None:
    """Choose a common encoder supported by the installed FFmpeg build."""
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    available = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 6:
            available.add(parts[1])
    for candidate in ("libx264", "libopenh264", "mpeg4"):
        if candidate in available:
            return candidate
    return None


def _transform_video(source: Path, destination: Path, matrix) -> bool:
    """Re-encode one intro with the same RGB transform and retain its audio."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or source.is_symlink() or not source.is_file():
        return False

    encoder = _available_video_encoder(ffmpeg)
    if encoder is None:
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
    ]
    if encoder == "libx264":
        command.extend(["-c:v", encoder, "-preset", "veryfast", "-crf", "20"])
    elif encoder == "libopenh264":
        command.extend(["-c:v", encoder, "-b:v", "5M", "-maxrate", "7M", "-bufsize", "10M"])
    else:
        command.extend(["-c:v", encoder, "-q:v", "3"])
    command.extend(["-c:a", "copy", "-map_metadata", "0", str(temporary)])
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


def only_recolored_asset_urls(assets: dict[str, str], branding_root: Path | None = None) -> dict[str, str]:
    """Drop source-file fallbacks so uncustomized colors never flash in LEOS UI."""
    originals = source_asset_urls(branding_root)
    return {
        key: url for key, url in assets.items()
        if isinstance(url, str) and url and url != originals.get(key)
    }


def _cache_directory(color_a: str, color_b: str, branding_root: Path) -> Path:
    fingerprints = []
    for relative in (
        "desktop-logo.jpeg", "gaming-logo.jpeg",
        "wallpapers/desktop-leos.svg", "wallpapers/gaming-leos.svg",
        "animations/desktop-intro.mov", "animations/gaming-intro.mp4",
    ):
        path = branding_root / relative
        try:
            info = path.stat()
            fingerprints.append(f"{relative}:{info.st_size}:{info.st_mtime_ns}")
        except OSError:
            fingerprints.append(f"{relative}:missing")
    source_fingerprint = "|".join(fingerprints)
    # Bump when logo masking/recoloring changes so stale opaque cache files
    # are never reused after a branding pipeline update.
    pair_id = hashlib.sha256(
        f"branding-pipeline-v2|{normalize_color(color_a)}|{normalize_color(color_b)}|{source_fingerprint}".encode("utf-8")
    ).hexdigest()[:20]
    return _cache_root() / pair_id


def cached_themed_branding_asset_urls(
    color_a: str,
    color_b: str,
    branding_root: Path | None = None,
) -> dict[str, str]:
    """Return ready cached variants and official source fallbacks without waiting."""
    root = branding_root or _branding_root()
    result = source_asset_urls(root)
    cache = _cache_directory(color_a, color_b, root)
    if cache.is_symlink() or not cache.is_dir():
        return result
    expected = {
        "desktopLogoUrl": cache / "desktop-logo.png",
        "gamingLogoUrl": cache / "gaming-logo.png",
        "desktopWallpaperUrl": cache / "desktop-leos.svg",
        "gamingWallpaperUrl": cache / "gaming-leos.svg",
        "desktopIntroUrl": cache / "desktop-intro.mov",
        "gamingIntroUrl": cache / "gaming-intro.mp4",
    }
    for key, path in expected.items():
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 0:
            result[key] = path.as_uri()
    return result


def build_themed_branding_assets(
    color_a: str,
    color_b: str,
    branding_root: Path | None = None,
    *,
    generate_videos: bool = True,
) -> dict[str, str]:
    """Build or reuse themed branding assets in a private cache directory."""
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    root = branding_root or _branding_root()
    original_urls = source_asset_urls(root)
    cache = _cache_directory(first, second, root)
    _safe_cache_directory(cache)

    lock_path = cache / ".build.lock"
    if lock_path.is_symlink():
        raise OSError("LEOS theme asset lock cannot be a symbolic link")

    matrix = build_color_matrix(first, second)
    with lock_path.open("a", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        # Wait for another LEOS process generating this same pair. Returning
        # source assets here could otherwise race first-run wallpaper setup.
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
                    output.as_uri() if output.is_file() and not output.is_symlink() and output.stat().st_size > 0
                    else original_urls["desktopWallpaperUrl" if key == "desktop_wallpaper" else "gamingWallpaperUrl"]
                )

            for key, filename in _VIDEO_NAMES.items():
                output = cache / filename
                source = root / "animations" / filename
                if output.is_symlink():
                    raise OSError("LEOS theme video cache cannot contain symbolic links")
                if generate_videos and (not output.is_file() or output.stat().st_size == 0):
                    _transform_video(source, output, matrix)
                assets["desktopIntroUrl" if key == "desktop_intro" else "gamingIntroUrl"] = (
                    output.as_uri() if output.is_file() and not output.is_symlink() and output.stat().st_size > 0
                    else original_urls["desktopIntroUrl" if key == "desktop_intro" else "gamingIntroUrl"]
                )
            return assets
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
