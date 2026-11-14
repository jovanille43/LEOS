#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -lt 2 || "$#" -gt 3 ]]; then
  echo "Usage: pin-image-digest.sh <ghcr-image:tag> <authfile> [output-file]" >&2
  exit 2
fi

image_ref="$1"
authfile="$2"
output_file="${3:-${GITHUB_OUTPUT:-}}"
podman_bin="${PODMAN_BIN:-podman}"

if [[ ! "$image_ref" =~ ^ghcr\.io/[a-z0-9][a-z0-9-]*/(leos|leos-nvidia|leos-nvidia-open):[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "::error::Refusing an unexpected LEOS image reference."
  exit 1
fi

if [[ ! -f "$authfile" ]]; then
  echo "::error::Container registry auth file is missing."
  exit 1
fi

if [[ -z "$output_file" ]]; then
  echo "::error::No GitHub Actions output file was provided."
  exit 1
fi

if ! command -v "$podman_bin" >/dev/null 2>&1; then
  echo "::error::Podman executable was not found."
  exit 1
fi

"$podman_bin" pull --authfile "$authfile" "$image_ref"
digest="$("$podman_bin" image inspect --format '{{.Digest}}' "$image_ref")"

if [[ ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::Podman did not return a valid SHA-256 image digest."
  exit 1
fi

image_repository="${image_ref%:*}"
printf 'ref=%s@%s\n' "$image_repository" "$digest" >> "$output_file"
echo "Pinned the selected LEOS image to immutable digest $digest."
