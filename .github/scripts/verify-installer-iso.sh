#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "Usage: verify-installer-iso.sh PATH_TO_ISO" >&2
  exit 64
fi

iso_input="$1"
if [[ ! -f "$iso_input" || ! -s "$iso_input" ]]; then
  echo "ISO is missing or empty: $iso_input" >&2
  exit 1
fi

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "sha256sum is required." >&2
  exit 1
fi
if ! command -v xorriso >/dev/null 2>&1; then
  echo "xorriso is required to inspect the boot catalog." >&2
  exit 1
fi

iso_path="$(realpath -- "$iso_input")"
checksum_name="$(basename -- "$iso_path").sha256"
checksum_path="$(dirname -- "$iso_path")/$checksum_name"
if [[ ! -s "$checksum_path" ]]; then
  echo "Expected checksum file is missing: $checksum_path" >&2
  exit 1
fi

(
  cd -- "$(dirname -- "$iso_path")"
  sha256sum --check --strict "$checksum_name"
)

report_file="$(mktemp)"
trap 'rm -f "$report_file"' EXIT
if ! xorriso -indev "$iso_path" -report_el_torito plain >"$report_file" 2>&1; then
  cat "$report_file" >&2
  echo "xorriso could not read the ISO El Torito boot catalog." >&2
  exit 1
fi

cat "$report_file"
if ! grep -Eiq "El Torito" "$report_file"; then
  echo "No El Torito boot catalog was found in the ISO." >&2
  exit 1
fi
if ! grep -Eiq "UEFI|0xEF" "$report_file"; then
  echo "The ISO does not advertise an UEFI El Torito boot entry." >&2
  exit 1
fi

echo "ISO integrity and UEFI boot-catalog checks passed."
