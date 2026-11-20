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

for tool in xorriso bsdtar unsquashfs; do
  command -v "$tool" >/dev/null 2>&1 || die "Required ISO inspection tool is missing: $tool"
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

if ! xorriso -indev "$iso_path" -report_el_torito plain >"$tmp_dir/el-torito.txt" 2>&1; then
  cat "$tmp_dir/el-torito.txt" >&2
  die "xorriso could not read the ISO El Torito boot catalog."
fi

# UEFI El Torito entries use Platform ID 0xef (239).
# xorriso versions differ: some report the EFI platform as numeric 0xef,
# while current releases print the decoded platform name "UEFI" in the
# El Torito boot-image table. Accept either explicit representation.
if ! grep -Eiq 'Platform Id[[:space:]]*:[[:space:]]*0xef([[:space:]]|$)|El Torito boot img[[:space:]]*:[[:space:]]*[0-9]+[[:space:]]+UEFI([[:space:]]|$)' "$tmp_dir/el-torito.txt"; then
  cat "$tmp_dir/el-torito.txt" >&2
  die "The ISO does not advertise a UEFI El Torito boot entry."
fi

if ! bsdtar -tf "$iso_path" | sed -E "s#^\\./##; s#^/##" >"$tmp_dir/iso-contents.txt"; then
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


# Inspect the SquashFS runtime embedded in the ISO. The package transaction in
# the build log is not sufficient: the final image must contain the WebUI.
if ! bsdtar -xOf "$iso_path" images/install.img >"$tmp_dir/install.img"; then
  die "Could not extract the Anaconda runtime image from the ISO."
fi

if ! unsquashfs -ll "$tmp_dir/install.img" >"$tmp_dir/runtime-contents.txt" 2>&1; then
  cat "$tmp_dir/runtime-contents.txt" >&2
  die "The Anaconda runtime image is not a readable SquashFS filesystem."
fi

required_webui_paths=(
  "usr/lib/systemd/system/webui-cockpit-ws.service"
  "usr/libexec/anaconda/webui-desktop"
  "usr/share/cockpit/anaconda-webui/index.html"
  "etc/anaconda/profile.d/fedora-server.conf"
)

for path in "${required_webui_paths[@]}"; do
  if ! grep -Fq "$path" "$tmp_dir/runtime-contents.txt"; then
    die "Required Anaconda WebUI runtime file is missing: $path"
  fi
  echo "Verified Anaconda WebUI runtime file: $path"
done

# The Fedora Kinoite profile hides account creation and expects first-boot
# setup. LEOS uses the Fedora Server installer profile so that account creation
# is available during installation.
server_profile="$tmp_dir/fedora-server.conf"
if ! unsquashfs -cat "$tmp_dir/install.img" etc/anaconda/profile.d/fedora-server.conf >"$server_profile"; then
  die "Could not read the Fedora Server Anaconda profile from the installer ISO."
fi

if ! grep -Fqx 'variant_id = server' "$server_profile"; then
  die "The installer ISO does not contain the expected Fedora Server Anaconda profile."
fi
if grep -Eq '^[[:space:]]*anaconda-screen-accounts([[:space:]]|$)' "$server_profile"; then
  die "The Anaconda profile hides account creation; refusing to publish this ISO."
fi

echo "Verified Anaconda Fedora Server profile and visible account-creation page."

echo "LEOS installer ISO structural validation passed."
echo "Note: VM boot, Anaconda UI, installation, and hardware compatibility still require separate tests."
