#!/usr/bin/env bash
set -Eeuo pipefail

readonly service_name="leos-root-fstab-fix.service"
readonly fstab="/etc/fstab"

disable_service() {
  systemctl disable "$service_name" || true
}

if [[ ! -f "$fstab" ]]; then
  echo "No /etc/fstab found; disabling the LEOS root mount workaround."
  disable_service
  exit 0
fi

rootflags_file="$(mktemp /run/leos-rootflags.XXXXXX)"
root_count_file="$(mktemp /run/leos-root-count.XXXXXX)"
cleanup() {
  rm -f "$rootflags_file" "$root_count_file"
}
trap cleanup EXIT

python3 - "$fstab" "$rootflags_file" "$root_count_file" <<'PY'
from pathlib import Path
import sys

fstab = Path(sys.argv[1])
flags_path = Path(sys.argv[2])
count_path = Path(sys.argv[3])
matches = []

for line in fstab.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    fields = stripped.split()
    if len(fields) >= 4 and fields[1] == "/":
        matches.append(fields[3])

if len(matches) > 1:
    raise SystemExit("More than one / entry exists in /etc/fstab; refusing to modify it.")

flags = []
if matches:
    ignored = {
        "defaults", "ro", "rw", "auto", "noauto", "nofail",
        "user", "users", "owner", "_netdev", "bind", "rbind",
    }
    for option in matches[0].split(","):
        if not option or option in ignored:
            continue
        if option.startswith(("x-systemd.", "x-fsck.", "comment=")):
            continue
        flags.append(option)

flags_path.write_text(",".join(flags), encoding="utf-8")
count_path.write_text(str(len(matches)), encoding="utf-8")
PY

root_count="$(< "$root_count_file")"
if [[ "$root_count" == "0" ]]; then
  echo "No root entry remains in /etc/fstab; disabling the LEOS workaround."
  disable_service
  exit 0
fi

rootflags="$(< "$rootflags_file")"
if [[ -n "$rootflags" ]]; then
  if ! command -v rpm-ostree >/dev/null 2>&1; then
    echo "rpm-ostree is required to preserve non-default root mount options."
    exit 1
  fi

  current_kargs="$(rpm-ostree kargs)"
  mapfile -t existing_rootflags < <(
    grep -oE '(^|[[:space:]])rootflags=[^[:space:]]+' <<< "$current_kargs" |
      sed -E 's/^[[:space:]]*rootflags=//'
  )
  if [[ "${#existing_rootflags[@]}" -gt 1 ]]; then
    echo "Multiple rootflags kernel arguments exist; refusing to guess which one to replace."
    exit 1
  fi
  if [[ "${#existing_rootflags[@]}" -eq 1 && "${existing_rootflags[0]}" != "$rootflags" ]]; then
    rpm-ostree kargs --delete-if-present="rootflags=${existing_rootflags[0]}"
  fi
  rpm-ostree kargs --append-if-missing="rootflags=$rootflags"
fi

# Remove only the root filesystem row. Keep /boot, /boot/efi, swap and data mounts.
python3 - "$fstab" <<'PY'
from pathlib import Path
import sys

fstab = Path(sys.argv[1])
lines = fstab.read_text(encoding="utf-8").splitlines(keepends=True)
kept = []
removed = 0

for line in lines:
    stripped = line.strip()
    fields = stripped.split() if stripped and not stripped.startswith("#") else []
    if len(fields) >= 2 and fields[1] == "/":
        removed += 1
    else:
        kept.append(line)

if removed != 1:
    raise SystemExit(f"Expected exactly one root fstab row, removed {removed}; refusing to continue.")

fstab.write_text("".join(kept), encoding="utf-8")
PY

disable_service
echo "LEOS root mount options have been moved to kernel arguments; rebooting once."
systemctl reboot
