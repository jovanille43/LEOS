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
skopeo_bin="${SKOPEO_BIN:-skopeo}"

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

for tool in "$skopeo_bin" "$podman_bin"; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "::error::Required image tool was not found: $tool"
    exit 1
  fi
done

# Skopeo reports the registry's top-level manifest/index digest. Podman's
# local .Digest can instead describe the architecture-specific child manifest.
digest="$("$skopeo_bin" inspect --authfile "$authfile" --format '{{.Digest}}' "docker://$image_ref")"
if [[ ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::Skopeo did not return a valid top-level SHA-256 manifest digest."
  exit 1
fi

image_repository="${image_ref%:*}"
immutable_ref="$image_repository@$digest"
"$podman_bin" pull --authfile "$authfile" "$immutable_ref"
"$podman_bin" tag "$immutable_ref" "$image_ref"

printf 'ref=%s\n' "$immutable_ref" >> "$output_file"
printf 'tag_ref=%s\n' "$image_ref" >> "$output_file"
echo "Pinned the selected LEOS image to immutable registry manifest digest $digest."
