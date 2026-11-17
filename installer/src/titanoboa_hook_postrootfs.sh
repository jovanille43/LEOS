#!/usr/bin/env bash
set -Eeuo pipefail

source /etc/os-release
: "${VARIANT_ID:?The Bazzite Live base must expose VARIANT_ID}"

target_local_ref="$(< /usr/share/leos-installer/install-image-local-ref)"
target_registry_ref="$(< /usr/share/leos-installer/install-image-registry-ref)"
target_digest="$(< /usr/share/leos-installer/install-image-digest)"
target_image_id="$(< /usr/share/leos-installer/install-image-id)"
target_cosign_key="/etc/pki/containers/leos-cosign.pub"

if [[ ! "$target_local_ref" =~ ^ghcr\.io/jovanille43/(leos|leos-nvidia|leos-nvidia-open):[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
  echo "::error::The embedded LEOS local image reference is invalid." >&2
  exit 1
fi
if [[ ! "$target_registry_ref" =~ ^ghcr\.io/jovanille43/(leos|leos-nvidia|leos-nvidia-open)@sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::The embedded LEOS registry reference is invalid." >&2
  exit 1
fi
if [[ ! "$target_digest" =~ ^sha256:[0-9a-f]{64}$ || "$target_registry_ref" != *"@$target_digest" ]]; then
  echo "::error::The embedded LEOS manifest digest is invalid." >&2
  exit 1
fi
if [[ ! "$target_image_id" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "::error::The embedded LEOS image ID is invalid." >&2
  exit 1
fi
if [[ "$target_registry_ref" != "${target_local_ref%:*}@$target_digest" ]]; then
  echo "::error::The embedded tag and digest references do not identify the same LEOS repository." >&2
  exit 1
fi

podman image exists "$target_local_ref"
# The local image ID is the architecture-specific config digest recorded after
# pulling the already-verified top-level registry manifest in the Live build.
live_image_id="$(podman image inspect --format '{{.Id}}' "$target_local_ref")"
if [[ "$live_image_id" != "$target_image_id" ]]; then
  echo "::error::The image available to Anaconda is not the verified LEOS payload." >&2
  exit 1
fi

dnf -qy versionlock clear || true
dnf install -qy --enable-repo=fedora-cisco-openh264 --allowerasing \
  firefox anaconda-live anaconda-dracut libblockdev-{btrfs,lvm,dm} yad
# Ensure Anaconda includes the Fedora fix for RHBZ 2332319 (bootc/OSTree root fstab handling).
dnf upgrade -qy anaconda-core anaconda-live anaconda-dracut
if rpm -q --changelog anaconda-dracut | grep -Eqi '2332319'; then
  echo "Anaconda contains the RHBZ 2332319 fix; the post-install root mount cleanup remains enabled."
else
  echo "::warning::Anaconda does not advertise the RHBZ 2332319 fix; the documented rootflags/fstab workaround will be applied to the installed deployment."
fi
install -d -m 0755 /var/lib/rpm-state /etc/anaconda/profile.d /etc/anaconda/conf.d
install -d -m 0755 /usr/share/anaconda/post-scripts

cat > /etc/anaconda/profile.d/leos.conf <<'EOF'
[Profile]
profile_id = leos

[Profile Detection]
os_id = bazzite

[Network]
default_on_boot = FIRST_WIRED_WITH_LINK

[Bootloader]
efi_dir = fedora
menu_auto_hide = False

[Storage]
default_scheme = BTRFS
btrfs_compression = zstd:1
default_partitioning =
    /     (min 1 GiB, max 70 GiB)
    /home (min 500 MiB, free 50 GiB)
    /var  (btrfs)

[User Interface]
hidden_webui_pages =
    network

[Localization]
use_geolocation = False
EOF

cat > /etc/anaconda/conf.d/leos.conf <<'EOF'
[Payload]
flatpak_remote = flathub https://dl.flathub.org/repo/
EOF

echo "LEOS installer based on Bazzite $VERSION_ID" > /etc/system-release

install -d -m 0755 /usr/share/ublue-os
curl --fail --location --retry 3 \
  -o /usr/share/ublue-os/sb_pubkey.der \
  https://github.com/ublue-os/akmods/raw/main/certs/public_key.der

cat > /usr/share/anaconda/post-scripts/leos-disable-fedora-flatpak.ks <<'EOF'
%post --erroronfail --log=/tmp/leos-install-logs/disable-fedora-flatpak.log
systemctl disable flatpak-add-fedora-repos.service || :
%end
EOF

cat > /usr/share/anaconda/post-scripts/leos-restore-selinux-labels.ks <<'EOF'
%post --erroronfail --log=/tmp/leos-install-logs/restore-selinux-labels.log
setenforce 0 || true
restorecon -R /etc/selinux
restorecon -R /var/lib/flatpak || true
%end
EOF

cat > /usr/share/anaconda/post-scripts/leos-secureboot-enroll-key.ks <<'EOF'
%post --erroronfail --nochroot --log=/tmp/leos-install-logs/secureboot-enroll-key.log
set -euo pipefail
readonly ENROLLMENT_PASSWORD="universalblue"
readonly SECUREBOOT_KEY="/usr/share/ublue-os/sb_pubkey.der"

if [[ ! -d /sys/firmware/efi || ! -s "$SECUREBOOT_KEY" ]]; then
  echo "Secure Boot key enrollment is not required in this boot mode."
  exit 0
fi

mokutil --timeout -1 || true
printf '%s\n%s\n' "$ENROLLMENT_PASSWORD" "$ENROLLMENT_PASSWORD" |
  mokutil --import "$SECUREBOOT_KEY" || true
%end
EOF

cat >> /usr/share/anaconda/interactive-defaults.ks <<'EOF'

%pre
mkdir -p /tmp/leos-install-logs
%end
EOF

cat > /usr/share/anaconda/post-scripts/leos-fstab-rootflags.ks <<'EOF'
%post --nochroot --erroronfail --log=/tmp/leos-install-logs/root-fstab-workaround-setup.log
set -euo pipefail

target_root="/mnt/sysroot"
if [[ ! -d "$target_root/etc" ]]; then
  echo "Anaconda did not mount the target system at /mnt/sysroot."
  exit 1
fi

install -D -m 0755 \
  /usr/share/leos-installer/leos-root-fstab-fix.sh \
  "$target_root/etc/leos/root-fstab-fix.sh"

cat > "$target_root/etc/systemd/system/leos-root-fstab-fix.service" <<'UNIT'
[Unit]
Description=LEOS first-boot bootc root filesystem compatibility fix
After=multi-user.target systemd-remount-fs.service bootc-fstab-edit.service
Before=graphical.target
ConditionPathExists=/etc/fstab

[Service]
Type=oneshot
ExecStart=/etc/leos/root-fstab-fix.sh
TimeoutStartSec=10min

[Install]
WantedBy=graphical.target
UNIT

install -d -m 0755 "$target_root/etc/systemd/system/graphical.target.wants"
ln -sfn ../leos-root-fstab-fix.service \
  "$target_root/etc/systemd/system/graphical.target.wants/leos-root-fstab-fix.service"
%end
EOF
cat >> /usr/share/anaconda/interactive-defaults.ks <<EOF
%pre --erroronfail --log=/tmp/leos-install-logs/preflight.log
set -euo pipefail
if [[ ! -d /sys/firmware/efi ]]; then
  echo "LEOS currently supports UEFI installation only."
  exit 1
fi
if ! podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s /etc/containers/policy.json; then
  echo "The LEOS image-signature policy is missing from the install payload."
  exit 1
fi
if ! podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s "$target_cosign_key"; then
  echo "The LEOS public verification key is missing from the install payload."
  exit 1
fi
if ! podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -x /usr/bin/rpm-ostree; then
  echo "The LEOS target image must include rpm-ostree for the first-boot root mount workaround."
  exit 1
fi
if ! command -v skopeo >/dev/null 2>&1; then
  echo "Skopeo is required to verify the LEOS update image before storage changes."
  exit 1
fi
remote_digest="$(skopeo inspect --format '{{.Digest}}' "docker://$target_local_ref")"
if [[ "$remote_digest" != "$target_digest" ]]; then
  echo "The LEOS update tag is unavailable or no longer points to the signed image embedded in this ISO."
  exit 1
fi
%end
EOF

cat >> /usr/share/anaconda/interactive-defaults.ks <<'EOF'
%pre-install --erroronfail --log=/tmp/leos-install-logs/boot-partition-check.log
set -euo pipefail
boot_source="$(findmnt --raw --noheadings --output SOURCE --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"
boot_fstype="$(findmnt --raw --noheadings --output FSTYPE --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"
boot_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"
root_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot 2>/dev/null || true)"
esp_fstype="$(findmnt --raw --noheadings --output FSTYPE --mountpoint /mnt/sysroot/boot/efi 2>/dev/null || true)"
esp_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot/boot/efi 2>/dev/null || true)"
if [[ -z "$boot_source" || -z "$boot_device" || -z "$root_device" ]]; then
  echo "LEOS requires explicit root and dedicated /boot mount points."
  exit 1
fi
if [[ "$boot_fstype" != "ext4" ]]; then
  echo "LEOS requires /boot on ext4; detected: ${boot_fstype:-unknown}"
  exit 1
fi
if [[ "$boot_device" == "$root_device" ]]; then
  echo "LEOS requires /boot to be on a partition separate from the root filesystem."
  exit 1
fi
if [[ -z "$esp_device" ]]; then
  echo "LEOS requires the EFI System Partition to be mounted at /boot/efi."
  exit 1
fi
if [[ "$esp_fstype" != "vfat" ]]; then
  echo "LEOS requires the EFI System Partition to use FAT (vfat); detected: ${esp_fstype:-unknown}"
  exit 1
fi
if [[ "$boot_device" == "$esp_device" ]]; then
  echo "LEOS requires /boot and /boot/efi to be separate partitions."
  exit 1
fi
%end
EOF

printf 'ostreecontainer --url=%s --transport=containers-storage --no-signature-verification\n' \
  "$target_local_ref" >> /usr/share/anaconda/interactive-defaults.ks
cat >> /usr/share/anaconda/interactive-defaults.ks <<'EOF'
%include /usr/share/anaconda/post-scripts/install-configure-upgrade.ks
%include /usr/share/anaconda/post-scripts/leos-fstab-rootflags.ks
%include /usr/share/anaconda/post-scripts/leos-disable-fedora-flatpak.ks
%include /usr/share/anaconda/post-scripts/leos-restore-selinux-labels.ks
%include /usr/share/anaconda/post-scripts/leos-secureboot-enroll-key.ks

%onerror
set +e
diagnostics_dir="/home/liveuser/Desktop/LEOS-installation-diagnostics"
mkdir -p "$diagnostics_dir"
summary_file="$diagnostics_dir/summary.txt"
: > "$summary_file"
mkdir -p /tmp/leos-install-logs
journalctl -b -n 1000 > /tmp/leos-install-logs/journalctl.log 2>&1 || true
log_files=(
  /tmp/anaconda.log
  /tmp/packaging.log
  /tmp/program.log
  /tmp/storage.log
  /tmp/syslog
  /tmp/leos-install-logs/*.log
)
for log_file in "${log_files[@]}"; do
  if [[ -s "$log_file" ]]; then
    printf '\n===== %s (last 200 lines) =====\n' "$log_file" >> "$summary_file"
    tail -n 200 "$log_file" >> "$summary_file"
    cp -f "$log_file" "$diagnostics_dir/"
  fi
done
if [[ -s "$summary_file" ]]; then
  tar -czf /home/liveuser/Desktop/LEOS-installation-diagnostics.tar.gz \
    -C /home/liveuser/Desktop LEOS-installation-diagnostics
  if id liveuser >/dev/null 2>&1; then
    chown -R liveuser:liveuser "$diagnostics_dir" \
      /home/liveuser/Desktop/LEOS-installation-diagnostics.tar.gz
    if command -v run0 >/dev/null 2>&1 && command -v yad >/dev/null 2>&1; then
      run0 --user=liveuser yad --title="Échec de l'installation LEOS" \
        --text-info --width=1000 --height=650 \
        --button="Fermer:0" < "$summary_file"
    fi
  fi
fi
%end
EOF

cat >> /usr/share/anaconda/post-scripts/install-configure-upgrade.ks <<EOF
%post --erroronfail --log=/tmp/leos-install-logs/bootc-switch.log
set -euo pipefail
test -s /etc/containers/policy.json
test -s $target_cosign_key
test -s /etc/containers/registries.d/leos.yaml
bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry "$target_local_ref"
%end
EOF

cat > /usr/bin/leos-live-welcome <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

image_tag_file="/usr/share/leos-installer/install-image-local-ref"
digest_file="/usr/share/leos-installer/install-image-digest"
if [[ ! -s "$image_tag_file" || ! -s "$digest_file" ]] || ! command -v skopeo >/dev/null 2>&1; then
  message="Le contrôle réseau de l'image LEOS est indisponible. L'installation est bloquée pour éviter un échec tardif."
  if command -v yad >/dev/null 2>&1; then
    yad --title="Précontrôle LEOS indisponible" --center --width=600 \
      --text="$message" --button="Fermer":0 || true
  else
    printf '%s\n' "$message"
  fi
  exit 0
fi

image_tag_ref="$(< "$image_tag_file")"
expected_digest="$(< "$digest_file")"
remote_digest="$(skopeo inspect --format '{{.Digest}}' "docker://$image_tag_ref" 2>/dev/null || true)"
if [[ "$remote_digest" != "$expected_digest" ]]; then
  message="Connexion à GHCR requise ou image candidate modifiée.\n\nLEOS doit vérifier que le tag $image_tag_ref pointe toujours vers le digest intégré à cette clé USB. Connectez le réseau puis relancez Installer LEOS depuis le menu KDE."
  if command -v yad >/dev/null 2>&1; then
    yad --title="Connexion requise avant installation" --center --width=680 \
      --text="$message" --button="Fermer":0 || true
  else
    printf '%b\n' "$message"
  fi
  exit 0
fi

status=0
if command -v yad >/dev/null 2>&1; then
  yad --title="Bienvenue dans LEOS" --center --width=560 \
    --text="Bienvenue dans l'environnement Live de LEOS.\n\nImage vérifiée : $image_tag_ref\n\nVous pouvez examiner le matériel avant de lancer l'installation. L'installation ne démarre qu'après votre choix." \
    --button="Installer LEOS":10 --button="Fermer":0 || status=$?
  if [[ "$status" -eq 10 ]]; then
    liveinst
  fi
else
  printf 'Image LEOS vérifiée : %s\n' "$image_tag_ref"
  liveinst
fi
EOF
chmod 0755 /usr/bin/leos-live-welcome
install -d -m 0755 /etc/skel/.config/autostart /usr/share/applications
cat > /etc/skel/.config/autostart/leos-live-welcome.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Bienvenue dans LEOS
Exec=/usr/bin/leos-live-welcome
Terminal=false
X-KDE-autostart-after=panel
EOF
cat > /usr/share/applications/leos-install.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Installer LEOS
Comment=Vérifier le réseau et l'image puis installer LEOS
Icon=system-software-install
Exec=/usr/bin/leos-live-welcome
Terminal=false
Categories=System;
EOF
chmod 0755 /usr/bin/leos-live-welcome
install -d -m 0755 /etc/skel/.config/autostart /usr/share/applications
cat > /etc/skel/.config/autostart/leos-live-welcome.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Bienvenue dans LEOS
Exec=/usr/bin/leos-live-welcome
Terminal=false
X-KDE-autostart-after=panel
EOF
cat > /usr/share/applications/leos-install.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Installer LEOS
Comment=Installer LEOS sur un disque choisi
Icon=system-software-install
Exec=liveinst
Terminal=false
Categories=System;
EOF

dnf clean all
