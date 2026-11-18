#!/usr/bin/env bash
# Fail closed if a generated LEOS installer ISO is incomplete or not UEFI bootable.
# This is a structural check; it does not replace a real VM or hardware install test.

set -euo pipefail

die() {
  echo "::error::$*" >&2
  exit 1
}

if [[ "$#" -ne 2 ]]; then
  die "Usage: $0 /path/to/LEOS.iso sha256:<verified-source-image-digest>"
fi

iso_input="$1"
expected_source_digest="$2"

if [[ ! -f "$iso_input" || -L "$iso_input" ]]; then
  die "ISO is missing, empty, or a symbolic link: $iso_input"
fi

if [[ ! "$expected_source_digest" =~ ^sha256:[a-f0-9]{64}$ ]]; then
  die "Expected source image digest is not a valid SHA-256 digest."
fi

iso_path="$(realpath -- "$iso_input")"
iso_dir="$(dirname -- "$iso_path")"
iso_name="$(basename -- "$iso_path")"
checksum_file="${iso_path}.sha256"
source_digest_file="${iso_path}.source-digest"

[[ -s "$iso_path" ]] || die "ISO file is empty."
[[ -s "$checksum_file" ]] || die "ISO SHA-256 checksum file is missing."
[[ -s "$source_digest_file" ]] || die "Verified source digest file is missing."

if ! (cd "$iso_dir" && sha256sum --check --strict "$iso_name.sha256"); then
  die "ISO SHA-256 verification failed."
fi

recorded_source_digest="$(<"$source_digest_file")"
if [[ "$recorded_source_digest" != "$expected_source_digest" ]]; then
  die "ISO source digest does not match the image digest verified before generation."
fi

for tool in xorriso bsdtar; do
  command -v "$tool" >/dev/null 2>&1 || die "Required ISO inspection tool is missing: $tool"
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

if ! xorriso -indev "$iso_path" -report_el_torito plain >"$tmp_dir/el-torito.txt" 2>&1; then
  cat "$tmp_dir/el-torito.txt" >&2
  die "xorriso could not read the ISO El Torito boot catalog."
fi

# UEFI El Torito entries use Platform ID 0xef (239).
if ! grep -Eiq 'Platform Id[[:space:]]*:[[:space:]]*0xef([[:space:]]|$)' "$tmp_dir/el-torito.txt"; then
  cat "$tmp_dir/el-torito.txt" >&2
  die "The ISO does not advertise a UEFI El Torito boot entry."
fi

if ! bsdtar -tf "$iso_path" >"$tmp_dir/iso-contents.txt"; then
  die "The ISO9660 filesystem could not be listed."
fi

required_paths=(
  "EFI/BOOT/BOOTX64.EFI"
  "EFI/BOOT/grub.cfg"
  "images/pxeboot/vmlinuz"
  "images/pxeboot/initrd.img"
  "images/install.img"
)

for path in "${required_paths[@]}"; do
  if ! grep -Fxq "$path" "$tmp_dir/iso-contents.txt"; then
    die "Required UEFI/Anaconda boot file is missing from the ISO: $path"
  fi
  echo "Verified ISO content: $path"
done

echo "LEOS installer ISO structural validation passed."
echo "Note: VM boot, Anaconda UI, installation, and hardware compatibility still require separate tests."
