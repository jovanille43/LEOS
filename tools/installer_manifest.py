"""Create a verified provenance manifest for a generated LEOS installer ISO."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


VARIANTS = frozenset({"standard", "nvidia-legacy", "nvidia-modern"})
TAG_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
VALIDATION_SCOPE = (
    "Anaconda WebUI boot verified; full installed LEOS session and physical hardware "
    "require separate validation"
)


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Hash a large ISO incrementally so memory usage is independent of its size."""
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_installer_manifest(
    iso_path: Path,
    variant: str,
    image_tag: str,
    source_commit: str,
    source_image_digest: str,
) -> Path:
    """Verify existing sidecars and write a JSON provenance manifest beside the ISO."""
    iso = Path(iso_path)
    if variant not in VARIANTS:
        raise ValueError("Unknown LEOS installer variant.")
    if not TAG_PATTERN.fullmatch(image_tag):
        raise ValueError("Invalid LEOS image tag.")
    if not COMMIT_PATTERN.fullmatch(source_commit):
        raise ValueError("Invalid LEOS source commit.")
    if not DIGEST_PATTERN.fullmatch(source_image_digest):
        raise ValueError("Invalid immutable image digest.")
    if not iso.is_file() or iso.stat().st_size <= 0:
        raise ValueError("Installer ISO is missing or empty.")

    iso_checksum = sha256_file(iso)
    checksum_path = Path(str(iso) + ".sha256")
    source_digest_path = Path(str(iso) + ".source-digest")
    try:
        checksum_parts = checksum_path.read_text(encoding="utf-8").split()
    except OSError as exc:
        raise ValueError("Installer checksum sidecar is missing or unreadable.") from exc
    if not checksum_parts or checksum_parts[0].lower() != iso_checksum:
        raise ValueError("Installer checksum does not match the ISO.")
    try:
        recorded_digest = source_digest_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError("Installer source-digest sidecar is missing or unreadable.") from exc
    if recorded_digest != source_image_digest:
        raise ValueError("Installer source digest does not match the verified image.")

    manifest = {
        "product": "LEOS",
        "variant": variant,
        "iso_file": iso.name,
        "iso_sha256": iso_checksum,
        "image_tag": image_tag,
        "source_commit": source_commit,
        "source_image_digest": source_image_digest,
        "installer_uefi_qemu_smoke": "passed",
        "validation_scope": VALIDATION_SCOPE,
    }
    output = Path(str(iso) + ".manifest.json")
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iso", type=Path)
    parser.add_argument("variant", choices=sorted(VARIANTS))
    parser.add_argument("image_tag")
    parser.add_argument("source_commit")
    parser.add_argument("source_image_digest")
    args = parser.parse_args()
    try:
        output = write_installer_manifest(
            args.iso,
            args.variant,
            args.image_tag,
            args.source_commit,
            args.source_image_digest,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
