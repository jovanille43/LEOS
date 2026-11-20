"""Build immutable, user-scoped A/B variants of KDE theme resources."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from desktop.branding_assets import build_color_matrix, transform_rgb
from desktop.themes import normalize_color


_HEX = re.compile(r"#[0-9A-Fa-f]{6}")
_VARIANT_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_MAX_FILES = 4096
_MAX_TOTAL_BYTES = 64 * 1024 * 1024
_MAX_FILE_BYTES = 8 * 1024 * 1024


def _hex_rgb(value: str) -> tuple[float, float, float]:
    value = normalize_color(value)
    return tuple(int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5))


def _recolor_svg(content: str, matrix) -> str:
    def recolor(match: re.Match[str]) -> str:
        rgb = transform_rgb(_hex_rgb(match.group(0)), matrix)
        channels = tuple(max(0, min(255, round(channel * 255))) for channel in rgb)
        return "#{:02X}{:02X}{:02X}".format(*channels)

    return _HEX.sub(recolor, content)


def create_recolored_theme_variant(
    source_root: Path,
    destination_parent: Path,
    base_id: str,
    color_a: str,
    color_b: str,
    *,
    metadata_kind: str,
) -> str:
    """Clone a packaged KDE theme, recolor only SVG accents, and install atomically.

    The source package and system directories are never modified. Each A/B pair
    receives its own deterministic KDE ID under the user's XDG data directory.
    """
    first = normalize_color(color_a)
    second = normalize_color(color_b)
    if not _VARIANT_ID.fullmatch(base_id):
        raise ValueError("Invalid base KDE theme identifier")
    if metadata_kind not in {"plasma", "icons"}:
        raise ValueError("Unsupported KDE theme metadata kind")
    if source_root.is_symlink() or not source_root.is_dir():
        raise FileNotFoundError("Packaged LEOS KDE theme directory is unavailable")

    entries = sorted(source_root.rglob("*"), key=lambda item: item.as_posix())
    if len(entries) > _MAX_FILES:
        raise ValueError("Packaged LEOS KDE theme contains too many files")

    digest = hashlib.sha256()
    source_files: list[tuple[Path, bytes]] = []
    total_bytes = 0
    for path in entries:
        if path.is_symlink():
            raise OSError("Symbolic links are not accepted in packaged LEOS KDE themes")
        relative = path.relative_to(source_root)
        if path.is_dir():
            continue
        if not path.is_file():
            raise OSError("Non-regular files are not accepted in packaged LEOS KDE themes")
        raw = path.read_bytes()
        total_bytes += len(raw)
        if len(raw) > _MAX_FILE_BYTES or total_bytes > _MAX_TOTAL_BYTES:
            raise ValueError("Packaged LEOS KDE theme exceeds its safe size limit")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(raw).digest())
        source_files.append((relative, raw))

    fingerprint = hashlib.sha256(
        f"{first}|{second}|".encode("ascii") + digest.digest()
    ).hexdigest()[:12]
    variant_id = f"{base_id}-ab-{fingerprint}"
    if not _VARIANT_ID.fullmatch(variant_id):
        raise ValueError("Generated KDE theme identifier is invalid")

    if destination_parent.is_symlink() or destination_parent.parent.is_symlink():
        raise OSError("LEOS KDE theme destination cannot contain a symbolic link")
    destination_parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination_parent.is_symlink() or not destination_parent.is_dir():
        raise OSError("LEOS KDE theme destination is not a regular directory")

    destination = destination_parent / variant_id
    manifest = {
        "schema_version": 1,
        "managed_by": "LEOS A/B Theme Variant Builder",
        "variant_id": variant_id,
        "source_fingerprint": fingerprint,
        "color_a": first,
        "color_b": second,
        "metadata_kind": metadata_kind,
    }
    marker_name = ".leos-ab-variant.json"
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise FileExistsError("A conflicting LEOS KDE theme path already exists")
        marker = destination / marker_name
        if marker.is_symlink() or not marker.is_file():
            raise FileExistsError("An unverified KDE theme variant already uses this identifier")
        try:
            existing = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            raise FileExistsError("An invalid KDE theme variant was left untouched")
        if existing != manifest:
            raise FileExistsError("A conflicting KDE theme variant was left untouched")
        return variant_id

    temporary = Path(tempfile.mkdtemp(prefix=".leos-ab-", dir=destination_parent))
    try:
        for path in entries:
            if path.is_dir():
                relative = path.relative_to(source_root)
                (temporary / relative).mkdir(parents=True, exist_ok=True, mode=0o700)

        matrix = build_color_matrix(first, second)
        for relative, raw in source_files:
            output = temporary / relative
            output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            payload = raw
            if output.suffix.lower() == ".svg":
                try:
                    content = raw.decode("utf-8")
                except UnicodeError as error:
                    raise ValueError(f"SVG is not UTF-8: {relative}") from error
                payload = _recolor_svg(content, matrix).encode("utf-8")
            elif metadata_kind == "plasma" and relative.as_posix() == "metadata.json":
                try:
                    metadata = json.loads(raw.decode("utf-8"))
                    plugin = metadata["KPlugin"]
                    if not isinstance(plugin, dict):
                        raise TypeError
                    plugin["Id"] = variant_id
                    plugin["Name"] = "LEOS personnalisé"
                    plugin["Description"] = "LEOS Plasma Style with the user's custom A/B gradient."
                    payload = (json.dumps(metadata, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
                except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
                    raise ValueError("LEOS Plasma Style metadata is invalid") from error
            elif metadata_kind == "icons" and relative.as_posix() == "index.theme":
                try:
                    content = raw.decode("utf-8")
                except UnicodeError as error:
                    raise ValueError("LEOS icon theme metadata is not UTF-8") from error
                content = re.sub(r"(?m)^Name=.*$", f"Name=LEOS personnalisé {fingerprint}", content, count=1)
                content = re.sub(r"(?m)^Comment=.*$", "Comment=LEOS user-selected A/B gradient", content, count=1)
                payload = content.encode("utf-8")

            with output.open("xb") as stream:
                stream.write(payload)
            os.chmod(output, 0o600)

        marker = temporary / marker_name
        with marker.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.chmod(marker, 0o600)
        for directory in sorted((item for item in temporary.rglob("*") if item.is_dir()), key=lambda item: len(item.parts), reverse=True):
            os.chmod(directory, 0o700)
        os.chmod(temporary, 0o700)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    return variant_id
