#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 3 ]]; then
  echo "Usage: sign-iso-artifacts.sh <iso-file> <provenance-json> <public-key>" >&2
  exit 2
fi

iso_file="$1"
provenance_file="$2"
public_key="$3"
iso_bundle="${iso_file}.sigstore.json"
provenance_bundle="${provenance_file}.sigstore.json"

for input in "$iso_file" "$provenance_file" "$public_key"; do
  if [[ ! -f "$input" || ! -s "$input" || -L "$input" ]]; then
    echo "::error::Required signing input is missing, empty, or not a regular file: $input" >&2
    exit 1
  fi
done

if [[ -z "${SIGNING_SECRET:-}" ]]; then
  echo "::error::The SIGNING_SECRET repository secret is not configured." >&2
  exit 1
fi

if ! command -v cosign >/dev/null 2>&1; then
  echo "::error::Cosign executable was not found." >&2
  exit 1
fi

if [[ -e "$iso_bundle" || -L "$iso_bundle" || -e "$provenance_bundle" || -L "$provenance_bundle" ]]; then
  echo "::error::Refusing to overwrite an existing Cosign bundle." >&2
  exit 1
fi

umask 077
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
chmod 700 "$workdir"

private_key="$workdir/cosign.key"
iso_bundle_tmp="$workdir/iso.sigstore.json"
provenance_bundle_tmp="$workdir/provenance.sigstore.json"

printf '%s' "$SIGNING_SECRET" > "$private_key"
chmod 600 "$private_key"
unset SIGNING_SECRET

cosign sign-blob \
  --yes \
  --key "$private_key" \
  --bundle "$iso_bundle_tmp" \
  "$iso_file"

cosign verify-blob \
  --key "$public_key" \
  --bundle "$iso_bundle_tmp" \
  "$iso_file"

cosign sign-blob \
  --yes \
  --key "$private_key" \
  --bundle "$provenance_bundle_tmp" \
  "$provenance_file"

cosign verify-blob \
  --key "$public_key" \
  --bundle "$provenance_bundle_tmp" \
  "$provenance_file"

install -m 0644 "$iso_bundle_tmp" "$iso_bundle"
install -m 0644 "$provenance_bundle_tmp" "$provenance_bundle"

echo "Cosign bundles created and verified for the LEOS ISO and provenance manifest."
