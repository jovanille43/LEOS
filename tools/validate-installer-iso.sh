#!/usr/bin/env bash
# Fail closed if a generated LEOS installer ISO is incomplete or not UEFI bootable.
# This is a structural check; it does not replace a complete VM installation test.

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
# while current releases print the decoded platform name "UEFI".
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

# Inspect the Anaconda runtime embedded in the ISO, not just the build logs.
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
)

for path in "${required_webui_paths[@]}"; do
  if ! grep -Fq "$path" "$tmp_dir/runtime-contents.txt"; then
    die "Required Anaconda WebUI runtime file is missing: $path"
  fi
  echo "Verified Anaconda WebUI runtime file: $path"
done

# The default BlueBuild Kinoite installer profile inherits Fedora KDE, whose
# WebUI profile hides the account-creation page. The Server installer variant
# uses Fedora's generic profile chain, where that page remains available.
server_profile="$tmp_dir/fedora-server.conf"
fedora_profile="$tmp_dir/fedora.conf"
installer_os_release="$tmp_dir/os-release"
if ! unsquashfs -cat "$tmp_dir/install.img" usr/lib/os-release >"$installer_os_release" 2>/dev/null; then
  die "Could not read the Anaconda installer OS identity."
fi

grep -Eq '^[[:space:]]*ID=fedora[[:space:]]*
  die "The Fedora Server Anaconda profile required for account creation is missing."
fi
if ! unsquashfs -cat "$tmp_dir/install.img" etc/anaconda/profile.d/fedora.conf >"$fedora_profile" 2>/dev/null; then
  die "The base Fedora Anaconda profile required by the Server profile is missing."
fi

grep -Eq '^[[:space:]]*profile_id[[:space:]]*=[[:space:]]*fedora-server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda runtime does not contain the expected fedora-server profile."
grep -Eq '^[[:space:]]*base_profile[[:space:]]*=[[:space:]]*fedora[[:space:]]*$' "$server_profile" ||
  die "The fedora-server profile does not inherit the generic Fedora profile."
grep -Eq '^[[:space:]]*variant_id[[:space:]]*=[[:space:]]*server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda Server profile does not match VARIANT_ID=server."
if grep -Eq '^[[:space:]]*anaconda-screen-accounts([[:space:]]|$)' "$server_profile" "$fedora_profile"; then
  die "The Anaconda account page is hidden by the selected Server profile chain."
fi
echo "Verified Fedora Server installer identity, selected Anaconda profile, and visible account-setup configuration."
echo "LEOS installer ISO structural validation passed."
echo "Note: complete installation, first boot, and hardware compatibility still require separate tests."
 "$installer_os_release" ||
  die "The installer OS identity is not Fedora."
grep -Eq '^[[:space:]]*VARIANT_ID=server[[:space:]]*
  die "The Fedora Server Anaconda profile required for account creation is missing."
fi
if ! unsquashfs -cat "$tmp_dir/install.img" etc/anaconda/profile.d/fedora.conf >"$fedora_profile" 2>/dev/null; then
  die "The base Fedora Anaconda profile required by the Server profile is missing."
fi

grep -Eq '^[[:space:]]*profile_id[[:space:]]*=[[:space:]]*fedora-server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda runtime does not contain the expected fedora-server profile."
grep -Eq '^[[:space:]]*base_profile[[:space:]]*=[[:space:]]*fedora[[:space:]]*$' "$server_profile" ||
  die "The fedora-server profile does not inherit the generic Fedora profile."
grep -Eq '^[[:space:]]*variant_id[[:space:]]*=[[:space:]]*server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda Server profile does not match VARIANT_ID=server."
if grep -Eq '^[[:space:]]*anaconda-screen-accounts([[:space:]]|$)' "$server_profile" "$fedora_profile"; then
  die "The Anaconda account page is hidden by the selected Server profile chain."
fi
echo "Verified Anaconda Server profile and visible account-setup configuration."
echo "LEOS installer ISO structural validation passed."
echo "Note: complete installation, first boot, and hardware compatibility still require separate tests."
 "$installer_os_release" ||
  die "The installer OS identity does not select the Fedora Server Anaconda profile."

if ! unsquashfs -cat "$tmp_dir/install.img" etc/anaconda/profile.d/fedora-server.conf >"$server_profile" 2>/dev/null; then
  die "The Fedora Server Anaconda profile required for account creation is missing."
fi
if ! unsquashfs -cat "$tmp_dir/install.img" etc/anaconda/profile.d/fedora.conf >"$fedora_profile" 2>/dev/null; then
  die "The base Fedora Anaconda profile required by the Server profile is missing."
fi

grep -Eq '^[[:space:]]*profile_id[[:space:]]*=[[:space:]]*fedora-server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda runtime does not contain the expected fedora-server profile."
grep -Eq '^[[:space:]]*base_profile[[:space:]]*=[[:space:]]*fedora[[:space:]]*$' "$server_profile" ||
  die "The fedora-server profile does not inherit the generic Fedora profile."
grep -Eq '^[[:space:]]*variant_id[[:space:]]*=[[:space:]]*server[[:space:]]*$' "$server_profile" ||
  die "The Anaconda Server profile does not match VARIANT_ID=server."
if grep -Eq '^[[:space:]]*anaconda-screen-accounts([[:space:]]|$)' "$server_profile" "$fedora_profile"; then
  die "The Anaconda account page is hidden by the selected Server profile chain."
fi
echo "Verified Anaconda Server profile and visible account-setup configuration."
echo "LEOS installer ISO structural validation passed."
echo "Note: complete installation, first boot, and hardware compatibility still require separate tests."
