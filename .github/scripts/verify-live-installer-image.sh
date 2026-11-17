#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "Usage: verify-live-installer-image.sh IMAGE_REF" >&2
  exit 64
fi
if [[ "$EUID" -ne 0 ]]; then
  echo "Run this check with root privileges so Podman can mount the image." >&2
  exit 1
fi
if ! command -v podman >/dev/null 2>&1; then
  echo "podman is required." >&2
  exit 1
fi

image_ref="$1"
if ! podman image exists "$image_ref"; then
  echo "Live installer image is not present in local Podman storage: $image_ref" >&2
  exit 1
fi

rootfs="$(podman image mount "$image_ref")"
if [[ -z "$rootfs" || ! -d "$rootfs" ]]; then
  echo "Podman could not mount the Live installer image." >&2
  exit 1
fi
cleanup() {
  podman image unmount "$image_ref" >/dev/null 2>&1 || true
}
trap cleanup EXIT

required_files=(
  "$rootfs/usr/lib/bootc-image-builder/iso.yaml"
  "$rootfs/usr/share/leos-installer/install-image-local-ref"
  "$rootfs/usr/share/leos-installer/install-image-registry-ref"
  "$rootfs/usr/share/leos-installer/install-image-digest"
  "$rootfs/usr/share/leos-installer/install-image-id"
  "$rootfs/usr/bin/skopeo"
)
for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Titanoboa contract file is missing or empty: ${file#"$rootfs"}" >&2
    exit 1
  fi
done

local_ref="$(< "$rootfs/usr/share/leos-installer/install-image-local-ref")"
registry_ref="$(< "$rootfs/usr/share/leos-installer/install-image-registry-ref")"
payload_digest="$(< "$rootfs/usr/share/leos-installer/install-image-digest")"
payload_image_id="$(< "$rootfs/usr/share/leos-installer/install-image-id")"
if [[ ! "$local_ref" =~ ^ghcr\.io/jovanille43/(leos|leos-nvidia|leos-nvidia-open):[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "The embedded LEOS tag reference is invalid." >&2
  exit 1
fi
if [[ ! "$payload_digest" =~ ^sha256:[0-9a-f]{64}$ || "$registry_ref" != "${local_ref%:*}@$payload_digest" ]]; then
  echo "The embedded LEOS digest and tag references do not match." >&2
  exit 1
fi
if [[ ! "$payload_image_id" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "The embedded LEOS image ID is invalid." >&2
  exit 1
fi

iso_config="$rootfs/usr/lib/bootc-image-builder/iso.yaml"
iso_label="$(awk -F: '/^label:/ { value=$2; gsub(/[ "]/, "", value); print value; exit }' "$iso_config")"
if [[ -z "$iso_label" ]]; then
  echo "The Titanoboa ISO configuration has no readable label." >&2
  exit 1
fi
if ! grep -Fq "root=live:CDLABEL=$iso_label" "$iso_config"; then
  echo "The GRUB entries do not reference the configured ISO label: $iso_label" >&2
  exit 1
fi

shopt -s nullglob
kernels=("$rootfs"/usr/lib/modules/*/vmlinuz)
if [[ "${#kernels[@]}" -ne 1 || ! -s "${kernels[0]:-}" ]]; then
  echo "Titanoboa requires exactly one non-empty /usr/lib/modules/*/vmlinuz; found ${#kernels[@]}." >&2
  printf '%s\n' "${kernels[@]}" >&2
  exit 1
fi
kernel_dir="$(dirname -- "${kernels[0]}")"
if [[ ! -s "$kernel_dir/initramfs.img" ]]; then
  echo "The initramfs.img matching the Live kernel is missing." >&2
  exit 1
fi

if [[ ! -s "$rootfs/usr/lib/grub/i386-pc/normal.mod" ]]; then
  echo "Titanoboa requires GRUB2 BIOS modules under /usr/lib/grub/i386-pc." >&2
  exit 1
fi
if [[ ! -s "$rootfs/usr/share/grub2/unicode.pf" ]]; then
  echo "Titanoboa requires /usr/share/grub2/unicode.pf from grub2-common." >&2
  exit 1
fi

efi_sources=("$rootfs"/usr/lib/efi/shim/*/EFI/fedora)
if [[ "${#efi_sources[@]}" -ne 1 ]]; then
  echo "Titanoboa requires exactly one Fedora UEFI vendor directory; found ${#efi_sources[@]}." >&2
  exit 1
fi
for efi_dir in "${efi_sources[@]}"; do
  for efi_binary in shimx64.efi mmx64.efi gcdx64.efi grubx64.efi; do
    if [[ ! -s "$efi_dir/$efi_binary" ]]; then
      echo "Required UEFI binary is missing: ${efi_dir#"$rootfs"}/$efi_binary" >&2
      exit 1
    fi
  done
done

for efi_binary in shimx64.efi mmx64.efi gcdx64.efi grubx64.efi; do
  if [[ ! -s "$rootfs/boot/efi/EFI/fedora/$efi_binary" ]]; then
    echo "Titanoboa boot EFI tree is missing $efi_binary." >&2
    exit 1
  fi
done

storage_roots=(
  "$rootfs/var/lib/containers/storage"
  "$rootfs/usr/lib/containers/storage"
)
storage_found=false
for storage_root in "${storage_roots[@]}"; do
  if [[ -d "$storage_root" ]] && find "$storage_root" -mindepth 1 -maxdepth 2 -print -quit | grep -q .; then
    storage_found=true
    break
  fi
done
if [[ "$storage_found" != true ]]; then
  echo "The Live image contains no embedded Podman image storage." >&2
  exit 1
fi

echo "Titanoboa Live image contract checks passed for $image_ref."
echo "ISO label: $iso_label"
echo "Kernel: ${kernel_dir#"$rootfs"}/vmlinuz"
echo "Initramfs: ${kernel_dir#"$rootfs"}/initramfs.img"
