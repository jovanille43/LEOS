"""Generate per-user A/B variants of the packaged Plasma Style and icon theme.

The read-only system themes are templates. This module creates uniquely named
user themes in XDG_DATA_HOME, recolors SVG accents with the same transform used
for LEOS logos/wallpapers, and never edits files below /usr/share.
"""
from __future__ import annotations

import configparser
import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from desktop.branding_assets import _transform_svg, build_color_matrix
from desktop.themes import normalize_color
from leos_core.paths import data_home as xdg_data_home

STYLE_SOURCE = Path("/usr/share/plasma/desktoptheme/leos")
ICON_SOURCE = Path("/usr/share/icons/leos")
_RESOURCE_ID = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
MAX_FILES = 2048
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 96 * 1024 * 1024
MANIFEST_NAME = ".leos-theme.json"


def _files(root: Path) -> list[tuple[Path, Path]]:
    if root.is_symlink() or not root.is_dir():
        raise FileNotFoundError(f"LEOS theme source is missing or unsafe: {root}")
    result: list[tuple[Path, Path]] = []
    total = 0
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        safe_directories = []
        for name in sorted(directories):
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"Symlink in LEOS theme source: {path}")
            safe_directories.append(name)
        directories[:] = safe_directories
        for name in sorted(filenames):
            path = current_path / name
            if path.is_symlink():
                raise OSError(f"Symlink in LEOS theme source: {path}")
            if not path.is_file():
                raise OSError(f"Non-regular LEOS theme source file: {path}")
            relative = path.relative_to(root)
            if not relative.parts or ".." in relative.parts:
                raise OSError("Invalid path in LEOS theme source")
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise OSError(f"LEOS theme source file is too large: {relative}")
            total += size
            if total > MAX_TOTAL_BYTES:
                raise OSError("LEOS theme source exceeds the total size limit")
            result.append((path, relative))
            if len(result) > MAX_FILES:
                raise OSError("LEOS theme source contains too many files")
    if not result:
        raise FileNotFoundError(f"LEOS theme source is empty: {root}")
    return result


def _source_fingerprint(style_files: list[tuple[Path, Path]], icon_files: list[tuple[Path, Path]]) -> str:
    digest = hashlib.sha256()
    for kind, entries in (("style", style_files), ("icons", icon_files)):
        digest.update(kind.encode("ascii"))
        for path, relative in entries:
            digest.update(relative.as_posix().encode("utf-8"))
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def _assert_no_symlink_components(path: Path, stop_at: Path) -> None:
    current = path
    stop = stop_at
    while True:
        if current.is_symlink():
            raise OSError(f"LEOS user theme path contains a symbolic link: {current}")
        if current == stop:
            return
        if current.parent == current:
            raise OSError("LEOS user theme path escaped its XDG data directory")
        current = current.parent


def _manifest(style_id: str, icon_id: str, color_a: str, color_b: str, fingerprint: str) -> dict[str, str]:
    return {
        "schema": "leos-themed-plasma-resources-v1",
        "style_id": style_id,
        "icon_id": icon_id,
        "color_a": color_a,
        "color_b": color_b,
        "source_fingerprint": fingerprint,
    }


def _read_manifest(directory: Path) -> dict[str, str] | None:
    if directory.is_symlink() or not directory.is_dir():
        return None
    path = directory / MANIFEST_NAME
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _write_manifest(directory: Path, payload: dict[str, str]) -> None:
    path = directory / MANIFEST_NAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o644)


def _copy_variant(
    source_files: list[tuple[Path, Path]],
    destination: Path,
    *,
    kind: str,
    theme_id: str,
    manifest: dict[str, str],
    matrix,
) -> None:
    if destination.is_symlink():
        raise OSError(f"User theme destination is a symbolic link: {destination}")
    if destination.exists():
        existing = _read_manifest(destination)
        if existing != manifest:
            raise FileExistsError(
                f"A different or incomplete theme already occupies {destination}; it was left untouched."
            )
        metadata = destination / ("metadata.json" if kind == "style" else "index.theme")
        if metadata.is_symlink() or not metadata.is_file():
            raise FileExistsError(f"Existing user theme is incomplete: {destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    if destination.parent.is_symlink():
        raise OSError(f"User theme parent is a symbolic link: {destination.parent}")
    staging = Path(tempfile.mkdtemp(prefix=f".{theme_id}.", dir=destination.parent))
    try:
        for source, relative in source_files:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            if relative.suffix.lower() == ".svg":
                if not _transform_svg(source, target, matrix, emblem=None):
                    raise OSError(f"Could not recolor LEOS SVG theme asset: {relative}")
            else:
                shutil.copyfile(source, target)
                os.chmod(target, 0o644)

        if kind == "style":
            metadata_path = staging / "metadata.json"
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            plugin = payload.get("KPlugin")
            if not isinstance(plugin, dict) or plugin.get("Id") != "leos":
                raise ValueError("The packaged LEOS Plasma Style metadata is invalid")
            plugin["Id"] = theme_id
            plugin["Name"] = "LEOS personnalisé"
            plugin["Description"] = "LEOS Plasma Style with the user's A/B accent gradient."
            metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            os.chmod(metadata_path, 0o644)
        else:
            index_path = staging / "index.theme"
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            parser.optionxform = str
            parser.read_string(index_path.read_text(encoding="utf-8"))
            if not parser.has_section("Icon Theme"):
                raise ValueError("The packaged LEOS icon theme index is invalid")
            parser.set("Icon Theme", "Name", "LEOS personnalisé")
            parser.set("Icon Theme", "Comment", "LEOS icons recolored with the user's A/B gradient")
            with index_path.open("w", encoding="utf-8") as stream:
                parser.write(stream)
            os.chmod(index_path, 0o644)

        _write_manifest(staging, manifest)
        for current, directories, filenames in os.walk(staging):
            os.chmod(current, 0o755)
            for filename in filenames:
                path = Path(current) / filename
                if not path.is_symlink():
                    os.chmod(path, 0o644)
        try:
            os.replace(staging, destination)
        except OSError:
            # A competing LEOS process may have installed this exact ID first.
            existing = _read_manifest(destination)
            if existing != manifest:
                raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def install_themed_plasma_resources(
    color_a: str,
    color_b: str,
    *,
    data_home: Path | None = None,
    plasma_theme_root: Path = STYLE_SOURCE,
    icon_theme_root: Path = ICON_SOURCE,
) -> dict[str, str]:
    """Install a matched per-user Plasma Style and icon theme for a chosen A/B pair."""
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    style_files = _files(plasma_theme_root)
    icon_files = _files(icon_theme_root)
    fingerprint = _source_fingerprint(style_files, icon_files)
    identity = hashlib.sha256(f"{first}|{second}|{fingerprint}".encode("utf-8")).hexdigest()[:16]
    style_id = f"leos-custom-{identity}"
    icon_id = f"leos-custom-{identity}"
    if not _RESOURCE_ID.fullmatch(style_id) or not _RESOURCE_ID.fullmatch(icon_id):
        raise ValueError("Generated LEOS theme identifier is invalid")

    base = Path(data_home) if data_home is not None else Path(xdg_data_home())
    base.mkdir(parents=True, exist_ok=True, mode=0o755)
    _assert_no_symlink_components(base, base)
    style_destination = base / "plasma" / "desktoptheme" / style_id
    icon_destination = base / "icons" / icon_id
    _assert_no_symlink_components(style_destination.parent, base)
    _assert_no_symlink_components(icon_destination.parent, base)
    manifest = _manifest(style_id, icon_id, first, second, fingerprint)
    matrix = build_color_matrix(first, second)

    lock_root = base / "leos" / "theme-resources"
    _assert_no_symlink_components(lock_root.parent, base)
    lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if lock_root.is_symlink():
        raise OSError("LEOS theme-resource lock directory cannot be a symbolic link")
    lock = lock_root / ".install.lock"
    if lock.is_symlink():
        raise OSError("LEOS theme-resource lock cannot be a symbolic link")
    with lock.open("a", encoding="utf-8") as stream:
        os.chmod(lock, 0o600)
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            _copy_variant(
                style_files, style_destination, kind="style",
                theme_id=style_id, manifest=manifest, matrix=matrix,
            )
            _copy_variant(
                icon_files, icon_destination, kind="icons",
                theme_id=icon_id, manifest=manifest, matrix=matrix,
            )
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    return {
        "plasmaStyleId": style_id,
        "iconThemeId": icon_id,
        "plasmaStylePath": str(style_destination),
        "iconThemePath": str(icon_destination),
    }
