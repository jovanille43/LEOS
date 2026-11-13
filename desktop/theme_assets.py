"""Generate user-scoped LEOS artwork variants from the official brand assets.

Only saturated pixels close to the two historical accent hues are shifted.
Alpha, brightness, saturation, neutral metallic details and geometry are kept.
The packaged PNG/SVG source files are never modified.
"""

from __future__ import annotations

import colorsys
import hashlib
import json
import os
import fcntl
import re
import shutil
import subprocess
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
    is_primary = primary_distance <= secondary_distance
    distance = primary_distance if is_primary else secondary_distance
    target = accent_primary if is_primary else accent_secondary
    source_base = "#00d9ff" if is_primary else "#e33bff"
    if distance > 58.0 / 360.0:
        return source.lower()

    target_rgb = tuple(
        int(target[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    source_base_rgb = tuple(
        int(source_base[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    target_hue, target_saturation, target_value = colorsys.rgb_to_hsv(*target_rgb)
    _base_hue, base_saturation, base_value = colorsys.rgb_to_hsv(*source_base_rgb)
    relative_saturation = saturation / base_saturation if base_saturation else 0.0
    relative_value = value / base_value if base_value else 0.0
    mapped_saturation = min(1.0, target_saturation * relative_saturation)
    mapped_value = min(1.0, target_value * relative_value)
    red, green, blue = colorsys.hsv_to_rgb(
        target_hue, mapped_saturation, mapped_value
    )
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
    for candidate in (path, *path.parents):
        if candidate.exists() and candidate.is_symlink():
            raise ValueError("Theme asset output path cannot contain symbolic links")
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
        emblem_path = Path(emblem_path)
        if emblem_path.parent.resolve() != output_path.parent.resolve():
            raise ValueError("Generated SVG emblem must be stored beside its wallpaper")
        emblem_name = emblem_path.name
        rendered = rendered.replace("../desktop-logo-alpha.png", emblem_name)
        rendered = rendered.replace("../gaming-logo-alpha.png", emblem_name)

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


def lut_cube_text(
    accent_primary: str,
    accent_secondary: str,
    size: int = 33,
) -> str:
    """Build a 3D LUT for FFmpeg that changes only the two source accent families."""
    if not _valid_hex(accent_primary) or not _valid_hex(accent_secondary):
        raise ValueError("Theme accent colors must be six-digit hexadecimal values")
    if type(size) is not int or not 2 <= size <= 65:
        raise ValueError("3D LUT size must be between 2 and 65")

    lines = [
        "TITLE \"LEOS two-accent theme\"",
        f"LUT_3D_SIZE {size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    primary_rgb = tuple(
        int(accent_primary[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    secondary_rgb = tuple(
        int(accent_secondary[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    primary_hue = colorsys.rgb_to_hsv(*primary_rgb)[0]
    secondary_hue = colorsys.rgb_to_hsv(*secondary_rgb)[0]
    source_primary_rgb = (0.0, 217 / 255.0, 1.0)
    source_secondary_rgb = (227 / 255.0, 59 / 255.0, 1.0)
    source_primary_saturation, source_primary_value = colorsys.rgb_to_hsv(*source_primary_rgb)[1:]
    source_secondary_saturation, source_secondary_value = colorsys.rgb_to_hsv(*source_secondary_rgb)[1:]

    # .cube ordering: red varies fastest, then green, then blue.
    for blue_index in range(size):
        blue = blue_index / (size - 1)
        for green_index in range(size):
            green = green_index / (size - 1)
            for red_index in range(size):
                red = red_index / (size - 1)
                hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
                if saturation < 0.16 or value < 0.14:
                    mapped = (red, green, blue)
                else:
                    primary_distance = _hue_distance(hue, _SOURCE_PRIMARY_HUE)
                    secondary_distance = _hue_distance(hue, _SOURCE_SECONDARY_HUE)
                    is_primary = primary_distance <= secondary_distance
                    distance = primary_distance if is_primary else secondary_distance
                    if distance > 58.0 / 360.0:
                        mapped = (red, green, blue)
                    elif is_primary:
                        mapped_saturation = min(
                            1.0,
                            colorsys.rgb_to_hsv(*primary_rgb)[1]
                            * saturation / source_primary_saturation,
                        )
                        mapped_value = min(
                            1.0,
                            colorsys.rgb_to_hsv(*primary_rgb)[2]
                            * value / source_primary_value,
                        )
                        mapped = colorsys.hsv_to_rgb(primary_hue, mapped_saturation, mapped_value)
                    else:
                        mapped_saturation = min(
                            1.0,
                            colorsys.rgb_to_hsv(*secondary_rgb)[1]
                            * saturation / source_secondary_saturation,
                        )
                        mapped_value = min(
                            1.0,
                            colorsys.rgb_to_hsv(*secondary_rgb)[2]
                            * value / source_secondary_value,
                        )
                        mapped = colorsys.hsv_to_rgb(secondary_hue, mapped_saturation, mapped_value)
                lines.append(" ".join(f"{channel:.7f}" for channel in mapped))
    return "\n".join(lines) + "\n"


def _write_private_text(path: Path, content: str) -> None:
    _safe_output_directory(path.parent)
    if path.is_symlink():
        raise ValueError("Theme cache files cannot be symbolic links")
    fd, temporary = tempfile.mkstemp(
        prefix="leos-lut-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def render_video_theme(
    source_path: Path,
    output_path: Path,
    lut_path: Path,
    timeout_seconds: int = 420,
) -> Path:
    """Re-encode a source animation through a selective two-accent 3D LUT.

    Audio is stream-copied. If FFmpeg or a supported encoder is unavailable,
    callers should keep using the official source animation unchanged.
    """
    source_path = Path(source_path)
    output_path = Path(output_path)
    lut_path = Path(lut_path)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("FFmpeg is not installed; use the official animation")
    if source_path.is_symlink() or not source_path.is_file():
        raise FileNotFoundError("Official LEOS animation is not a regular file")
    if lut_path.is_symlink() or not lut_path.is_file():
        raise FileNotFoundError("Generated LEOS color LUT is not available")
    _safe_output_directory(output_path.parent)
    if output_path.is_symlink():
        raise ValueError("Theme video cache cannot be a symbolic link")

    fd, temporary = tempfile.mkstemp(
        prefix="leos-video-", suffix=".mp4", dir=output_path.parent
    )
    os.close(fd)
    command_base = [
        ffmpeg,
        "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-i", str(source_path),
        "-vf", f"lut3d=file={lut_path.name}:interp=tetrahedral",
        "-map", "0:v:0", "-map", "0:a?",
        "-map_metadata", "0",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
    ]
    last_error = ""
    try:
        for encoder_args in (
            ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "192k"],
            ["-c:v", "mpeg4", "-q:v", "3", "-c:a", "aac", "-b:a", "192k"],
        ):
            try:
                result = subprocess.run(
                    command_base[:8] + encoder_args + command_base[8:],
                    cwd=output_path.parent,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                last_error = str(error)
                continue
            if result.returncode == 0 and Path(temporary).is_file() and Path(temporary).stat().st_size > 0:
                os.chmod(temporary, 0o600)
                os.replace(temporary, output_path)
                return output_path
            last_error = (result.stderr or "FFmpeg could not encode the themed animation")[-2000:]
        raise RuntimeError(last_error or "No supported FFmpeg video encoder is available")
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


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

    def _output_dir_for_theme(self, theme: str) -> Path:
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        fingerprint = hashlib.sha256(
            (
                theme
                + palette["accent_primary"]
                + palette["accent_secondary"]
            ).encode("ascii")
        ).hexdigest()[:16]
        output_dir = self.cache_dir / "leos" / "themes" / fingerprint
        _safe_output_directory(output_dir)
        return output_dir

    def paths_for_theme(self, theme: str) -> dict[str, str]:
        """Generate logos and wallpapers quickly; never wait for video encoding."""
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        if (
            palette["accent_primary"].lower() == "#00d9ff"
            and palette["accent_secondary"].lower() == "#e33bff"
        ):
            return {
                "desktop_logo": (self.branding_dir / "desktop-logo-alpha.png").resolve().as_uri(),
                "gaming_logo": (self.branding_dir / "gaming-logo-alpha.png").resolve().as_uri(),
                "desktop_wallpaper": (self.branding_dir / "wallpapers" / "desktop-leos.svg").resolve().as_uri(),
                "gaming_wallpaper": (self.branding_dir / "wallpapers" / "gaming-leos.svg").resolve().as_uri(),
            }

        output_dir = self._output_dir_for_theme(theme)
        desktop_logo = output_dir / "desktop-logo.png"
        gaming_logo = output_dir / "gaming-logo.png"
        desktop_wallpaper = output_dir / "desktop-wallpaper.svg"
        gaming_wallpaper = output_dir / "gaming-wallpaper.svg"

        if not desktop_logo.is_file() or desktop_logo.is_symlink():
            render_logo_theme(
                self.branding_dir / "desktop-logo-alpha.png", desktop_logo, palette
            )
        if not gaming_logo.is_file() or gaming_logo.is_symlink():
            render_logo_theme(
                self.branding_dir / "gaming-logo-alpha.png", gaming_logo, palette
            )
        if not desktop_wallpaper.is_file() or desktop_wallpaper.is_symlink():
            render_svg_theme(
                self.branding_dir / "wallpapers" / "desktop-leos.svg",
                desktop_wallpaper,
                palette,
                desktop_logo,
            )
        if not gaming_wallpaper.is_file() or gaming_wallpaper.is_symlink():
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

    def video_paths_for_theme(self, theme: str) -> dict[str, str]:
        """Generate both themed introductions in an independent background task.

        If FFmpeg is unavailable or encoding fails, that animation independently
        falls back to its official source. Image and UI recoloring never waits.
        """
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        desktop_source = self.branding_dir / "animations" / "desktop-intro.mov"
        gaming_source = self.branding_dir / "animations" / "gaming-intro.mp4"
        if (
            palette["accent_primary"].lower() == "#00d9ff"
            and palette["accent_secondary"].lower() == "#e33bff"
        ):
            return {
                "desktop_intro": desktop_source.resolve().as_uri(),
                "gaming_intro": gaming_source.resolve().as_uri(),
                "videos_recolored": "true",
            }

        output_dir = self._output_dir_for_theme(theme)
        lut_path = output_dir / "theme.cube"
        if not lut_path.is_file() or lut_path.is_symlink():
            _write_private_text(
                lut_path,
                lut_cube_text(palette["accent_primary"], palette["accent_secondary"]),
            )
        outputs = {}
        for key, source, filename in (
            ("desktop_intro", desktop_source, "desktop-intro.mp4"),
            ("gaming_intro", gaming_source, "gaming-intro.mp4"),
        ):
            destination = output_dir / filename
            if destination.is_symlink():
                raise ValueError("Theme video cache cannot be a symbolic link")
            if not destination.is_file() or destination.stat().st_size == 0:
                try:
                    render_video_theme(source, destination, lut_path)
                except (FileNotFoundError, RuntimeError, OSError, ValueError):
                    # Original animation remains playable and is never altered.
                    pass
            outputs[key] = (
                destination.resolve().as_uri()
                if destination.is_file() and destination.stat().st_size > 0
                else source.resolve().as_uri()
            )
        videos_recolored = all(
            (output_dir / filename).is_file()
            and (output_dir / filename).stat().st_size > 0
            for filename in ("desktop-intro.mp4", "gaming-intro.mp4")
        )
        outputs["videos_recolored"] = str(videos_recolored).lower()
        status = {
            "version": 1,
            "theme": theme,
            "videos_recolored": videos_recolored,
            "desktop_generated": outputs["desktop_intro"].startswith(output_dir.resolve().as_uri()),
            "gaming_generated": outputs["gaming_intro"].startswith(output_dir.resolve().as_uri()),
        }
        _write_private_text(
            output_dir / ".videos-ready.json",
            json.dumps(status, ensure_ascii=False, separators=(",", ":")) + "\n",
        )
        return outputs

    def cached_video_paths_for_theme(self, theme: str) -> dict[str, str] | None:
        """Read completed video variants only after the background worker publishes status."""
        output_dir = self._output_dir_for_theme(theme)
        status_path = output_dir / ".videos-ready.json"
        if status_path.is_symlink() or not status_path.is_file():
            return None
        try:
            raw = status_path.read_bytes()
            if len(raw) > 8192:
                return None
            status = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            return None
        if (
            not isinstance(status, dict)
            or status.get("version") != 1
            or status.get("theme") != theme
            or type(status.get("videos_recolored")) is not bool
        ):
            return None
        desktop_source = self.branding_dir / "animations" / "desktop-intro.mov"
        gaming_source = self.branding_dir / "animations" / "gaming-intro.mp4"
        desktop_generated = output_dir / "desktop-intro.mp4"
        gaming_generated = output_dir / "gaming-intro.mp4"
        return {
            "desktop_intro": (
                desktop_generated.resolve().as_uri()
                if status.get("desktop_generated") is True
                and desktop_generated.is_file()
                and not desktop_generated.is_symlink()
                else desktop_source.resolve().as_uri()
            ),
            "gaming_intro": (
                gaming_generated.resolve().as_uri()
                if status.get("gaming_generated") is True
                and gaming_generated.is_file()
                and not gaming_generated.is_symlink()
                else gaming_source.resolve().as_uri()
            ),
            "videos_recolored": str(status["videos_recolored"]).lower(),
        }


def _generate_video_worker(theme: str) -> int:
    """Serialize video generation so concurrently running LEOS apps share one job."""
    manager = ThemeAssetManager()
    output_dir = manager._output_dir_for_theme(theme)
    lock_path = output_dir / ".video-generation.lock"
    if lock_path.is_symlink():
        return 1
    with lock_path.open("a", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        manager.video_paths_for_theme(theme)
    return 0


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="LEOS theme asset worker")
    parser.add_argument("--generate-videos", metavar="THEME")
    args = parser.parse_args()
    if not args.generate_videos:
        parser.error("A worker action is required")
    try:
        return _generate_video_worker(args.generate_videos)
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(_main())
