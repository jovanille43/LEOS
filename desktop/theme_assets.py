"""Generate user-scoped LEOS artwork variants from the official brand assets.

The original two-colour gradient is mapped continuously to the selected pair.
Glow falloff, luminance, alpha, neutral metallic details and geometry are kept.
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

from desktop.themes import THEME_NAMES, THEME_PALETTES, palette_for_theme
from leos_core.paths import data_home as xdg_data_home

_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
_SOURCE_PRIMARY_RGB = (0.0, 217.0 / 255.0, 1.0)
_SOURCE_SECONDARY_RGB = (227.0 / 255.0, 59.0 / 255.0, 1.0)
_SOURCE_PRIMARY_HSV = colorsys.rgb_to_hsv(*_SOURCE_PRIMARY_RGB)
_SOURCE_SECONDARY_HSV = colorsys.rgb_to_hsv(*_SOURCE_SECONDARY_RGB)
_SOURCE_PRIMARY_HUE = _SOURCE_PRIMARY_HSV[0]
_SOURCE_SECONDARY_HUE = _SOURCE_SECONDARY_HSV[0]
_ACCENT_HUE_TOLERANCE = 58.0 / 360.0
_MAX_SVG_BYTES = 4 * 1024 * 1024
_MAX_IMAGE_PIXELS = 18_000_000


def _valid_hex(value: str) -> bool:
    return isinstance(value, str) and _HEX_COLOR.fullmatch(value) is not None


def _accent_position(hue: float) -> float | None:
    """Return the position between the source accents, including soft end caps."""
    source_span = (_SOURCE_SECONDARY_HUE - _SOURCE_PRIMARY_HUE) % 1.0
    offset = (hue - _SOURCE_PRIMARY_HUE) % 1.0
    if offset <= source_span:
        return offset / source_span

    before_primary = 1.0 - offset
    after_secondary = offset - source_span
    if min(before_primary, after_secondary) > _ACCENT_HUE_TOLERANCE:
        return None
    return 0.0 if before_primary <= after_secondary else 1.0


def _target_hsv_pair(
    accent_primary: str,
    accent_secondary: str,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if not _valid_hex(accent_primary) or not _valid_hex(accent_secondary):
        raise ValueError("Theme accent colors must be six-digit hexadecimal values")
    primary_rgb = tuple(
        int(accent_primary[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    secondary_rgb = tuple(
        int(accent_secondary[index:index + 2], 16) / 255.0 for index in (1, 3, 5)
    )
    return colorsys.rgb_to_hsv(*primary_rgb), colorsys.rgb_to_hsv(*secondary_rgb)


def _map_accent_rgb(
    rgb: tuple[float, float, float],
    target_primary: tuple[float, float, float],
    target_secondary: tuple[float, float, float],
) -> tuple[float, float, float] | None:
    """Map both source accent families through one continuous gradient function."""
    hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
    if saturation < 0.16 or value < 0.14:
        return None

    position = _accent_position(hue)
    if position is None:
        return None

    target_hue_delta = (
        (target_secondary[0] - target_primary[0] + 0.5) % 1.0
    ) - 0.5
    mapped_hue = (target_primary[0] + position * target_hue_delta) % 1.0

    source_saturation = (
        _SOURCE_PRIMARY_HSV[1] * (1.0 - position)
        + _SOURCE_SECONDARY_HSV[1] * position
    )
    target_saturation = (
        target_primary[1] * (1.0 - position)
        + target_secondary[1] * position
    )
    source_value = (
        _SOURCE_PRIMARY_HSV[2] * (1.0 - position)
        + _SOURCE_SECONDARY_HSV[2] * position
    )
    target_value = (
        target_primary[2] * (1.0 - position)
        + target_secondary[2] * position
    )

    mapped_saturation = min(
        1.0, target_saturation * saturation / max(source_saturation, 1e-9)
    )
    mapped_value = min(1.0, target_value * value / max(source_value, 1e-9))
    return colorsys.hsv_to_rgb(mapped_hue, mapped_saturation, mapped_value)


def recolor_hex_color(
    source: str,
    accent_primary: str,
    accent_secondary: str,
) -> str:
    """Re-map the original two-colour gradient without a midpoint colour split.

    Pixels between the cyan and magenta source anchors are interpolated
    continuously between the selected accents. Saturation/value and alpha
    handling preserve the original glow falloff, metallic highlights and
    luminance structure; neutrals and unrelated hues are left untouched.
    """
    if not _valid_hex(source):
        raise ValueError("Source asset color must be a six-digit hexadecimal value")
    target_primary, target_secondary = _target_hsv_pair(
        accent_primary, accent_secondary
    )
    rgb = tuple(int(source[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    mapped = _map_accent_rgb(rgb, target_primary, target_secondary)
    if mapped is None:
        return source.lower()
    return "#{:02x}{:02x}{:02x}".format(
        *(round(channel * 255) for channel in mapped)
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
    size: int = 49,
) -> str:
    """Build a high-resolution LUT using the exact same smooth gradient mapping."""
    if type(size) is not int or not 2 <= size <= 65:
        raise ValueError("3D LUT size must be between 2 and 65")
    target_primary, target_secondary = _target_hsv_pair(
        accent_primary, accent_secondary
    )
    lines = [
        "TITLE \"LEOS smooth two-accent gradient\"",
        f"LUT_3D_SIZE {size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]

    # .cube ordering: red varies fastest, then green, then blue.
    for blue_index in range(size):
        blue = blue_index / (size - 1)
        for green_index in range(size):
            green = green_index / (size - 1)
            for red_index in range(size):
                red = red_index / (size - 1)
                source_rgb = (red, green, blue)
                mapped = _map_accent_rgb(
                    source_rgb, target_primary, target_secondary
                )
                if mapped is None:
                    mapped = source_rgb
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

    Audio is preserved and encoded to AAC for MP4 compatibility. If FFmpeg or
    a supported encoder is unavailable,
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
                    command_base[:8] + encoder_args + command_base[8:] + [temporary],
                    cwd=output_path.parent,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                    shell=False,
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


_SVG_PAINT_ATTRIBUTE = re.compile(
    r'(?P<prefix>\b(?:stop-color|stroke|fill)\s*=\s*["\']|(?:stop-color|stroke|fill)\s*:\s*)'
    r'(?P<color>#[0-9A-Fa-f]{6})(?P<suffix>["\']?)',
    re.IGNORECASE,
)


def recolor_kde_svg_markup(
    markup: str,
    accent_primary: str,
    accent_secondary: str,
) -> str:
    """Recolor bright KDE SVG accents while protecting dark and slate neutrals.

    Gradient stops retain the full source-gradient mapping. Standalone fills
    and strokes are recolored only when bright and sufficiently saturated,
    so inactive slate outlines and dark window/widget surfaces remain intact.
    """
    if not isinstance(markup, str) or len(markup.encode("utf-8")) > _MAX_SVG_BYTES:
        raise ValueError("KDE SVG source is invalid or exceeds its size limit")
    if not _valid_hex(accent_primary) or not _valid_hex(accent_secondary):
        raise ValueError("Theme accent colors must be six-digit hexadecimal values")

    def replace(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        color = match.group("color")
        attribute = prefix.lower().split("=", 1)[0].split(":", 1)[0].strip()
        rgb = tuple(
            int(color[index:index + 2], 16) / 255.0
            for index in (1, 3, 5)
        )
        _hue, saturation, value = colorsys.rgb_to_hsv(*rgb)
        if saturation < 0.42 or value < 0.30:
            return match.group(0)
        recolored = recolor_hex_color(
            color, accent_primary, accent_secondary
        )
        return f"{prefix}{recolored}{match.group('suffix')}"

    return _SVG_PAINT_ATTRIBUTE.sub(replace, markup)


def _replace_ini_section_values(
    markup: str,
    section: str,
    values: Mapping[str, str],
) -> str:
    """Replace required keys in one INI section without reformatting the file."""
    lines = markup.splitlines()
    active_section = ""
    remaining = set(values)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            active_section = stripped[1:-1]
            continue
        if active_section != section or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key not in remaining:
            continue
        indentation = line[: len(line) - len(line.lstrip())]
        lines[index] = f"{indentation}{key}={values[key]}"
        remaining.remove(key)
    if remaining:
        raise ValueError(
            f"Theme metadata is missing required keys in [{section}]: "
            + ", ".join(sorted(remaining))
        )
    result = "\n".join(lines)
    return result + ("\n" if markup.endswith("\n") else "")


def render_kde_theme_package(
    source_dir: Path,
    output_dir: Path,
    palette: Mapping[str, str],
    theme: str,
    package_kind: str,
) -> Path:
    """Build a recolored, distinctly named KDE resource package in user cache.

    The source package is read-only. Every SVG is copied and selectively
    recolored; metadata receives a unique package ID so KDE can distinguish
    each generated variant. A lock and atomic directory rename protect
    concurrent LEOS processes from observing a partially copied package.
    """
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    if theme not in THEME_NAMES:
        raise ValueError(f"Unknown LEOS theme: {theme}")
    if package_kind not in {"icons", "plasma", "aurorae"}:
        raise ValueError("Unsupported KDE theme package type")
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise FileNotFoundError("Official LEOS KDE resource directory is unavailable")
    if not _valid_hex(palette.get("accent_primary", "")) or not _valid_hex(
        palette.get("accent_secondary", "")
    ):
        raise ValueError("Theme accent colors must be six-digit hexadecimal values")

    theme_label = THEME_NAMES[theme].removeprefix("LEOS ")
    display_name = f"LEOS — {theme_label}"
    package_id = f"leos-{theme}"
    expected_manifest = {
        "version": 1,
        "theme": theme,
        "kind": package_kind,
        "package_id": package_id,
    }

    _safe_output_directory(output_dir.parent)
    if output_dir.is_symlink():
        raise ValueError("Generated KDE theme package cannot be a symbolic link")
    lock_path = output_dir.parent / f".{output_dir.name}.lock"
    if lock_path.is_symlink():
        raise ValueError("Generated KDE theme lock cannot be a symbolic link")

    with lock_path.open("a", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

        if output_dir.exists():
            if not output_dir.is_dir() or output_dir.is_symlink():
                raise ValueError("Generated KDE theme destination is not a safe directory")
            manifest_path = output_dir / ".leos-theme-package.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                manifest = None
            if manifest == expected_manifest:
                return output_dir
            shutil.rmtree(output_dir)

        temporary = Path(
            tempfile.mkdtemp(prefix=f"leos-{package_kind}-", dir=output_dir.parent)
        )
        try:
            for current, directories, files in os.walk(
                source_dir, topdown=True, followlinks=False
            ):
                current_path = Path(current)
                relative_dir = current_path.relative_to(source_dir)
                target_dir = temporary / relative_dir
                target_dir.mkdir(parents=True, exist_ok=True)

                for directory in directories:
                    if (current_path / directory).is_symlink():
                        raise ValueError("KDE source package contains a symbolic-link directory")

                for filename in sorted(files):
                    original = current_path / filename
                    if original.is_symlink() or not original.is_file():
                        raise ValueError("KDE source package contains a non-regular file")
                    relative_file = original.relative_to(source_dir)
                    if relative_file.is_absolute() or ".." in relative_file.parts:
                        raise ValueError("KDE source package contains an unsafe path")
                    destination = temporary / relative_file
                    destination.parent.mkdir(parents=True, exist_ok=True)

                    if original.suffix.lower() == ".svg":
                        markup = original.read_text(encoding="utf-8")
                        rendered = recolor_kde_svg_markup(
                            markup,
                            palette["accent_primary"],
                            palette["accent_secondary"],
                        )
                        destination.write_text(rendered, encoding="utf-8")
                    elif original.name == "index.theme":
                        markup = original.read_text(encoding="utf-8")
                        rendered = _replace_ini_section_values(
                            markup,
                            "Icon Theme",
                            {
                                "Name": display_name,
                                "Comment": f"LEOS icon theme — {theme_label}",
                            },
                        )
                        destination.write_text(rendered, encoding="utf-8")
                    elif original.name == "metadata.desktop":
                        markup = original.read_text(encoding="utf-8")
                        rendered = _replace_ini_section_values(
                            markup,
                            "Desktop Entry",
                            {
                                "Name": display_name,
                                "Comment": f"LEOS window decoration — {theme_label}",
                                "X-KDE-PluginInfo-Name": package_id,
                            },
                        )
                        destination.write_text(rendered, encoding="utf-8")
                    elif original.name == "metadata.json":
                        metadata = json.loads(original.read_text(encoding="utf-8"))
                        plugin = metadata.get("KPlugin")
                        if not isinstance(plugin, dict):
                            raise ValueError("Plasma theme metadata has no KPlugin object")
                        plugin["Id"] = package_id
                        plugin["Name"] = display_name
                        plugin["Description"] = (
                            f"LEOS Plasma style with the {theme_label} two-accent palette."
                        )
                        destination.write_text(
                            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
                    else:
                        shutil.copyfile(original, destination)

            manifest_path = temporary / ".leos-theme-package.json"
            manifest_path.write_text(
                json.dumps(expected_manifest, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            os.chmod(manifest_path, 0o600)
            os.replace(temporary, output_dir)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)

    return output_dir




def _validate_generated_package(
    package_dir: Path,
    theme: str,
    package_kind: str,
) -> None:
    """Reject incomplete, modified or unsafe generated KDE package trees."""
    if package_dir.is_symlink() or not package_dir.is_dir():
        raise ValueError("Generated KDE package is not a safe directory")
    manifest_path = package_dir / ".leos-theme-package.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("Generated KDE package manifest is unavailable")
    try:
        manifest_raw = manifest_path.read_bytes()
        if len(manifest_raw) > 8192:
            raise ValueError("Generated KDE package manifest exceeds its size limit")
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Generated KDE package manifest is invalid") from error

    expected = {
        "version": 1,
        "theme": theme,
        "kind": package_kind,
        "package_id": f"leos-{theme}",
    }
    if manifest != expected:
        raise ValueError("Generated KDE package does not match the requested theme")

    for current, directories, files in os.walk(
        package_dir, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        for dirname in directories:
            if (current_path / dirname).is_symlink():
                raise ValueError("Generated KDE package contains a symbolic-link directory")
        for filename in files:
            candidate = current_path / filename
            if candidate.is_symlink() or not candidate.is_file():
                raise ValueError("Generated KDE package contains an unsafe file")


def _package_trees_equal(first: Path, second: Path) -> bool:
    """Compare two already validated package trees without following symlinks."""
    def inventory(root: Path) -> dict[str, Path]:
        result: dict[str, Path] = {}
        for current, directories, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            for dirname in directories:
                directory = current_path / dirname
                if directory.is_symlink() or not directory.is_dir():
                    raise ValueError("KDE package contains an unsafe directory")
            for filename in files:
                path = current_path / filename
                if path.is_symlink() or not path.is_file():
                    raise ValueError("KDE package contains an unsafe file")
                result[path.relative_to(root).as_posix()] = path
        return result

    left = inventory(first)
    right = inventory(second)
    if left.keys() != right.keys():
        return False
    return all(left[key].read_bytes() == right[key].read_bytes() for key in left)


def _copy_package_atomically(
    source: Path,
    destination: Path,
    theme: str,
    package_kind: str,
) -> Path:
    """Export one verified KDE package without replacing any existing files."""
    _validate_generated_package(source, theme, package_kind)
    destination = Path(destination)
    parent = destination.parent

    if destination.name != f"leos-{theme}":
        raise ValueError("KDE package destination does not match its LEOS identifier")

    # Refuse symlinked or non-directory ancestors, including an XDG root that
    # points outside the path the user explicitly configured.
    ancestors: list[Path] = []
    current = parent
    while True:
        ancestors.append(current)
        if current.parent == current:
            break
        current = current.parent
    for directory in reversed(ancestors):
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise ValueError("KDE user data path contains an unsafe directory")
        if not directory.exists():
            directory.mkdir(mode=0o755)

    lock_path = parent / f".{destination.name}.leos-export.lock"
    if lock_path.is_symlink():
        raise ValueError("KDE export lock cannot be a symbolic link")
    with lock_path.open("a", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

        if destination.is_symlink():
            raise FileExistsError("A symbolic link already uses this KDE theme name")
        if destination.exists():
            if not destination.is_dir():
                raise FileExistsError("A non-directory entry already uses this KDE theme name")
            _validate_generated_package(destination, theme, package_kind)
            if not _package_trees_equal(source, destination):
                raise FileExistsError(
                    "A different KDE theme already uses this LEOS identifier; it was left untouched."
                )
            return destination

        temporary = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.leos-", dir=parent)
        )
        try:
            for current, directories, files in os.walk(
                source, topdown=True, followlinks=False
            ):
                relative = Path(current).relative_to(source)
                target_dir = temporary / relative
                target_dir.mkdir(parents=True, exist_ok=True)
                for dirname in directories:
                    candidate = Path(current) / dirname
                    if candidate.is_symlink():
                        raise ValueError("Generated KDE package contains a symbolic-link directory")
                for filename in files:
                    original = Path(current) / filename
                    if original.is_symlink() or not original.is_file():
                        raise ValueError("Generated KDE package contains an unsafe file")
                    target = target_dir / filename
                    shutil.copyfile(original, target)
                    os.chmod(target, 0o644)
                os.chmod(target_dir, 0o755)

            _validate_generated_package(temporary, theme, package_kind)
            try:
                os.rename(temporary, destination)
            except FileExistsError:
                if not destination.is_dir() or destination.is_symlink():
                    raise
                _validate_generated_package(destination, theme, package_kind)
                if not _package_trees_equal(source, destination):
                    raise FileExistsError(
                        "A different KDE theme appeared during export; it was left untouched."
                    )
        finally:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)

    return destination


class ThemeAssetManager:
    """Create cached logo and wallpaper copies without touching packaged assets."""

    def __init__(
        self,
        branding_dir: Path | None = None,
        cache_dir: Path | None = None,
        icon_theme_dir: Path | None = None,
        plasma_theme_dir: Path | None = None,
        aurorae_theme_dir: Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[1]
        self.branding_dir = branding_dir or project_root / "branding"

        def resource_dir(
            supplied: Path | None,
            repository_path: str,
            installed_path: str,
        ) -> Path:
            if supplied is not None:
                return Path(supplied)
            candidate = project_root / repository_path
            return candidate if candidate.is_dir() else Path(installed_path)

        self.icon_theme_dir = resource_dir(
            icon_theme_dir, "icons/leos", "/usr/share/icons/leos"
        )
        self.plasma_theme_dir = resource_dir(
            plasma_theme_dir,
            "plasma-theme/leos",
            "/usr/share/plasma/desktoptheme/leos",
        )
        self.aurorae_theme_dir = resource_dir(
            aurorae_theme_dir,
            "aurorae/leos",
            "/usr/share/aurorae/themes/leos",
        )
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
        source_files = (
            self.branding_dir / "desktop-logo-alpha.png",
            self.branding_dir / "gaming-logo-alpha.png",
            self.branding_dir / "wallpapers" / "desktop-leos.svg",
            self.branding_dir / "wallpapers" / "gaming-leos.svg",
            self.branding_dir / "animations" / "desktop-intro.mov",
            self.branding_dir / "animations" / "gaming-intro.mp4",
        )
        source_versions = []
        for source in source_files:
            try:
                info = source.stat()
                source_versions.append(
                    f"branding/{source.name}:{info.st_size}:{info.st_mtime_ns}"
                )
            except OSError:
                source_versions.append(f"branding/{source.name}:missing")

        for label, source_dir in (
            ("icons", self.icon_theme_dir),
            ("plasma", self.plasma_theme_dir),
            ("aurorae", self.aurorae_theme_dir),
        ):
            if source_dir.is_symlink() or not source_dir.is_dir():
                source_versions.append(f"{label}:missing-or-unsafe")
                continue
            for source in sorted(source_dir.rglob("*")):
                relative = source.relative_to(source_dir).as_posix()
                if source.is_symlink():
                    source_versions.append(f"{label}/{relative}:symlink")
                    continue
                if source.is_file():
                    try:
                        info = source.stat()
                        source_versions.append(
                            f"{label}/{relative}:{info.st_size}:{info.st_mtime_ns}"
                        )
                    except OSError:
                        source_versions.append(f"{label}/{relative}:unreadable")
        fingerprint = hashlib.sha256(
            (
                theme
                + palette["accent_primary"]
                + palette["accent_secondary"]
                + "|".join(source_versions)
            ).encode("utf-8")
        ).hexdigest()[:16]
        output_dir = self.cache_dir / "leos" / "themes" / fingerprint
        _safe_output_directory(output_dir)
        return output_dir

    def kde_resource_paths_for_theme(self, theme: str) -> dict[str, str]:
        """Generate cached icon, Plasma Style and Aurorae variants without applying them."""
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        if (
            palette["accent_primary"].lower() == "#00d9ff"
            and palette["accent_secondary"].lower() == "#e33bff"
        ):
            return {}

        output_dir = self._output_dir_for_theme(theme) / "kde"
        package_id = f"leos-{theme}"
        definitions = (
            ("icon_theme", "icons", self.icon_theme_dir),
            ("plasma_theme", "plasma", self.plasma_theme_dir),
            ("aurorae_theme", "aurorae", self.aurorae_theme_dir),
        )
        assets: dict[str, str] = {}
        for asset_key, package_kind, source_dir in definitions:
            if not source_dir.is_dir() or source_dir.is_symlink():
                continue
            package_path = render_kde_theme_package(
                source_dir,
                output_dir / package_kind / package_id,
                palette,
                theme,
                package_kind,
            )
            assets[f"{asset_key}_path"] = str(package_path)
            assets[f"{asset_key}_name"] = package_id
        return assets

    def exported_kde_resource_paths_for_theme(
        self,
        theme: str,
        data_directory: Path | None = None,
    ) -> dict[str, str]:
        """Return the complete set of safely exported KDE packages, if present."""
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        palette = palette_for_theme(theme)
        if (
            palette["accent_primary"].lower() == "#00d9ff"
            and palette["accent_secondary"].lower() == "#e33bff"
        ):
            return {}

        data_root = Path(data_directory) if data_directory is not None else Path(
            xdg_data_home()
        )
        if not data_root.is_absolute() or ".." in data_root.parts or data_root.is_symlink():
            return {}
        package_id = f"leos-{theme}"
        definitions = (
            ("icon_theme_path", "icons", Path("icons") / package_id),
            (
                "plasma_theme_path",
                "plasma",
                Path("plasma") / "desktoptheme" / package_id,
            ),
            (
                "aurorae_theme_path",
                "aurorae",
                Path("aurorae") / "themes" / package_id,
            ),
        )
        result: dict[str, str] = {}
        for key, package_kind, relative_path in definitions:
            package = data_root / relative_path
            try:
                _validate_generated_package(package, theme, package_kind)
            except (OSError, ValueError):
                return {}
            result[key] = str(package)
        return result

    def export_kde_resource_packages_for_theme(
        self,
        theme: str,
        data_directory: Path | None = None,
    ) -> dict[str, str]:
        """Copy generated KDE variants into XDG user paths, without activating them.

        Existing differing packages are never overwritten. This method only
        prepares user-local packages; selection remains a separate KDE action.
        """
        if theme not in THEME_PALETTES:
            raise ValueError(f"Unknown LEOS theme: {theme}")
        if (
            palette_for_theme(theme)["accent_primary"].lower() == "#00d9ff"
            and palette_for_theme(theme)["accent_secondary"].lower() == "#e33bff"
        ):
            return {}

        cached = self.kde_resource_paths_for_theme(theme)
        if not cached:
            return {}
        required = {"icon_theme_path", "plasma_theme_path", "aurorae_theme_path"}
        if not required.issubset(cached):
            raise FileNotFoundError("One or more LEOS KDE theme source packages are unavailable")

        data_root = Path(data_directory) if data_directory is not None else Path(
            xdg_data_home()
        )
        if not data_root.is_absolute() or ".." in data_root.parts:
            raise ValueError("XDG data directory must be an absolute normalized path")
        package_id = f"leos-{theme}"
        destinations = (
            ("icon_theme_path", "icons", Path("icons") / package_id),
            (
                "plasma_theme_path",
                "plasma",
                Path("plasma") / "desktoptheme" / package_id,
            ),
            (
                "aurorae_theme_path",
                "aurorae",
                Path("aurorae") / "themes" / package_id,
            ),
        )
        exported: dict[str, str] = {}
        for source_key, package_kind, relative_destination in destinations:
            source_text = cached.get(source_key)
            if not source_text:
                continue
            source = Path(source_text)
            destination = data_root / relative_destination
            copied = _copy_package_atomically(
                source,
                destination,
                theme,
                package_kind,
            )
            exported[source_key] = str(copied)
        return exported

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

        assets = {
            "desktop_logo": desktop_logo.as_uri(),
            "gaming_logo": gaming_logo.as_uri(),
            "desktop_wallpaper": desktop_wallpaper.as_uri(),
            "gaming_wallpaper": gaming_wallpaper.as_uri(),
        }
        assets.update(self.kde_resource_paths_for_theme(theme))
        return assets

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
