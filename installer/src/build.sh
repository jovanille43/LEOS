#!/usr/bin/bash
set -Eeuo pipefail
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly INSTALL_IMAGE_REF="${INSTALL_IMAGE_REF:?INSTALL_IMAGE_REF is required}"
readonly INSTALL_IMAGE_TAG_REF="${INSTALL_IMAGE_TAG_REF:?INSTALL_IMAGE_TAG_REF is required}"
readonly INSTALL_IMAGE_DIGEST="${INSTALL_IMAGE_DIGEST:?INSTALL_IMAGE_DIGEST is required}"
readonly REGISTRY_AUTH_FILE="${REGISTRY_AUTH_FILE:?REGISTRY_AUTH_FILE is required}"

if [[ ! "$INSTALL_IMAGE_REF" =~ ^ghcr\.io/jovanille43/(leos|leos-nvidia|leos-nvidia-open)@sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::Unexpected immutable LEOS image reference: $INSTALL_IMAGE_REF" >&2
  exit 1
fi
if [[ ! "$INSTALL_IMAGE_TAG_REF" =~ ^ghcr\.io/jovanille43/(leos|leos-nvidia|leos-nvidia-open):[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "::error::Unexpected LEOS image tag reference: $INSTALL_IMAGE_TAG_REF" >&2
  exit 1
fi
if [[ "$INSTALL_IMAGE_REF" != "${INSTALL_IMAGE_TAG_REF%:*}@$INSTALL_IMAGE_DIGEST" ]]; then
  echo "::error::The immutable image reference and expected digest do not match." >&2
  exit 1
fi
if [[ ! -r "$REGISTRY_AUTH_FILE" ]]; then
  echo "::error::The temporary GHCR authentication secret is not readable." >&2
  exit 1
fi

podman pull --authfile "$REGISTRY_AUTH_FILE" "$INSTALL_IMAGE_REF"
pulled_digest="$(podman image inspect --format '{{.Digest}}' "$INSTALL_IMAGE_REF")"
if [[ "$pulled_digest" != "$INSTALL_IMAGE_DIGEST" ]]; then
  echo "::error::The downloaded image does not match the verified digest." >&2
  exit 1
fi
pulled_id="$(podman image inspect --format '{{.Id}}' "$INSTALL_IMAGE_REF")"
if [[ ! "$pulled_id" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::Podman did not return a valid immutable image ID." >&2
  exit 1
fi
podman tag "$INSTALL_IMAGE_REF" "$INSTALL_IMAGE_TAG_REF"

podman save --format oci-archive "$INSTALL_IMAGE_TAG_REF" |
  podman load --storage-opt additionalimagestore=''
loaded_id="$(podman image inspect --format '{{.Id}}' "$INSTALL_IMAGE_TAG_REF")"
if [[ "$loaded_id" != "$pulled_id" ]]; then
  echo "::error::The image embedded in the Live environment changed during storage import." >&2
  exit 1
fi

install -d -m 0755 /usr/share/leos-installer
printf '%s\n' "$INSTALL_IMAGE_TAG_REF" > /usr/share/leos-installer/install-image-local-ref
printf '%s\n' "$INSTALL_IMAGE_REF" > /usr/share/leos-installer/install-image-registry-ref
printf '%s\n' "$INSTALL_IMAGE_DIGEST" > /usr/share/leos-installer/install-image-digest
printf '%s\n' "$pulled_id" > /usr/share/leos-installer/install-image-id
chmod 0644 /usr/share/leos-installer/install-image-*

bash "$SCRIPT_DIR/titanoboa_hook_preinitramfs.sh"
dnf install -y dracut-live
mapfile -t kernels < <(kernel-install list --json pretty | jq -r '.[] | select(.has_kernel == true) | .version' | sort -Vu)
if [[ "${#kernels[@]}" -ne 1 ]]; then
  echo "::error::Expected exactly one Live kernel; found ${#kernels[@]}." >&2
  printf '%s\n' "${kernels[@]}" >&2
  exit 1
fi
kernel="${kernels[0]}"
DRACUT_NO_XATTR=1 dracut -v --force --reproducible --no-hostonly \
  --add "dmsquash-live dmsquash-live-autooverlay" \
  "/usr/lib/modules/${kernel}/initramfs.img" "$kernel"

dnf install -y livesys-scripts
sed -i 's/^livesys_session=.*/livesys_session=kde/' /etc/sysconfig/livesys
systemctl enable livesys.service livesys-late.service
bash "$SCRIPT_DIR/titanoboa_hook_postrootfs.sh"

dnf install -y grub2-efi-x64-cdboot
install -d -m 0755 /boot/efi
cp -av /usr/lib/efi/*/*/EFI /boot/efi/
if [[ -f /boot/efi/EFI/fedora/grubx64.efi ]]; then
  install -D -m 0644 /boot/efi/EFI/fedora/grubx64.efi /boot/efi/EFI/BOOT/fbx64.efi
fi

rm -f /etc/localtime
systemd-firstboot --timezone UTC
rm -rf /var/tmp
install -d -m 1777 /var/tmp
cat > /etc/systemd/system/var-tmp.mount <<'EOF'
[Unit]
Description=Larger tmpfs for /var/tmp on the LEOS Live system
[Mount]
What=tmpfs
Where=/var/tmp
Type=tmpfs
Options=size=50%%,nr_inodes=1m,x-systemd.graceful-option=usrquota
[Install]
WantedBy=local-fs.target
EOF
systemctl enable var-tmp.mount

if [[ -L /mnt ]]; then rm -f /mnt; fi
install -d -m 0755 /mnt
install -d -m 0755 /usr/lib/bootc-image-builder
install -m 0644 "$SCRIPT_DIR/iso.yaml" /usr/lib/bootc-image-builder/iso.yaml
dnf clean all
