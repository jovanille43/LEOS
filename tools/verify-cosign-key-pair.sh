#!/usr/bin/env bash
# Verify that a local Cosign private key matches the public key without
# publishing an image, uploading to the transparency log, or exposing either key.
# Uses the Cosign v3 signing-config interface and a service-free config.

set -euo pipefail

private_key="${1:-cosign.key}"
public_key="${2:-cosign.pub}"

if [[ ! -f "$private_key" || -L "$private_key" || ! -s "$private_key" ]]; then
  echo "::error::Private key file is missing, empty, or a symbolic link: $private_key" >&2
  exit 1
fi
if [[ ! -f "$public_key" || -L "$public_key" || ! -s "$public_key" ]]; then
  echo "::error::Public key file is missing, empty, or a symbolic link: $public_key" >&2
  exit 1
fi
if ! command -v cosign >/dev/null 2>&1; then
  echo "::error::Cosign is not installed or is not available in PATH." >&2
  exit 1
fi

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
chmod 700 "$workdir"
printf 'LEOS signing-key preflight\n' > "$workdir/challenge.txt"

# This is a local key-pair check only. Use no Sigstore services so the
# synthetic challenge is never uploaded to a public transparency log.
cosign signing-config create \
  --no-default-fulcio \
  --no-default-rekor \
  --no-default-oidc \
  --no-default-tsa \
  --out "$workdir/signing-config.json"
cosign sign-blob \
  --key "$private_key" \
  --signing-config "$workdir/signing-config.json" \
  --bundle "$workdir/challenge.bundle" \
  --yes \
  "$workdir/challenge.txt"
cosign verify-blob \
  --key "$public_key" \
  --insecure-ignore-tlog \
  --bundle "$workdir/challenge.bundle" \
  "$workdir/challenge.txt"

printf 'Cosign private/public key pair verified successfully.\n'
