#!/usr/bin/env bash
set -Eeuo pipefail

kernel_packages=(
  kernel
  kernel-core
  kernel-devel
  kernel-devel-matched
  kernel-modules
  kernel-modules-core
  kernel-modules-extra
)

dnf -y versionlock delete "${kernel_packages[@]}" || true
dnf --setopt=protect_running_kernel=False -y remove "${kernel_packages[@]}"
rm -rf -- /usr/lib/modules/*
dnf -y --repo=fedora,updates --setopt=tsflags=noscripts install kernel kernel-core

mapfile -t kernel_versions < <(
  find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -Vu
)
if [[ "${#kernel_versions[@]}" -ne 1 ]]; then
  echo "::error::Expected one Fedora kernel for the Live ISO." >&2
  printf '%s\n' "${kernel_versions[@]}" >&2
  exit 1
fi
depmod "${kernel_versions[0]}"

dnf install -yq nvidia-gpu-firmware || true
dnf clean all
