"""Contract tests for the Titanoboa-based LEOS installer pipeline."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "installer"
WORKFLOW = ROOT / ".github/workflows/iso-titanoboa.yml"


class TitanoboaInstallerTests(unittest.TestCase):
    def test_installer_shell_scripts_have_valid_bash_syntax(self):
        for script in (
            INSTALLER / "src/build.sh",
            INSTALLER / "src/titanoboa_hook_preinitramfs.sh",
            INSTALLER / "src/titanoboa_hook_postrootfs.sh",
            INSTALLER / "src/leos-root-fstab-fix.sh",
            ROOT / ".github/scripts/verify-live-installer-image.sh",
            ROOT / ".github/scripts/pin-image-digest.sh",
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    ["bash", "-n", str(script)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_bazzite_base_signature_uses_the_pinned_upstream_key_format(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        documentation = (ROOT / "docs/titanoboa-installer.md").read_text(encoding="utf-8")
        key = (ROOT / "files/bazzite-cosign.pub").read_text(encoding="utf-8")
        self.assertEqual(
            key,
            "-----BEGIN PUBLIC KEY-----\n"
            "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEHLRpBfPRYiMl9wb7s6fx47PzzNWu\n"
            "3zyJgXhWEvxoOgwv9CpwjbvUwR9qHxNMWkJhuGE6cjDA2hpy1I6NbA+24Q==\n"
            "-----END PUBLIC KEY-----\n",
        )
        self.assertIn("cosign verify --key files/bazzite-cosign.pub --new-bundle-format=false", workflow)
        self.assertIn("f8580007fb1fb4241378fd99b33800aefe62c3b5", documentation)

    def test_pin_image_digest_uses_skopeo_registry_manifest_digest(self):
        script = ROOT / ".github/scripts/pin-image-digest.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            authfile = root / "auth.json"
            authfile.write_text("{}", encoding="utf-8")
            output_file = root / "github-output"
            podman_log = root / "podman.log"
            digest = "sha256:" + "a" * 64

            skopeo = bin_dir / "skopeo"
            skopeo.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\n' \"$*\" > \"$SKOPEO_LOG\"\n"
                f"printf '%s\n' '{digest}'\n",
                encoding="utf-8",
            )
            podman = bin_dir / "podman"
            podman.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\n' \"$*\" >> \"$PODMAN_LOG\"\n",
                encoding="utf-8",
            )
            skopeo.chmod(0o755)
            podman.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "SKOPEO_BIN": str(skopeo),
                    "PODMAN_BIN": str(podman),
                    "SKOPEO_LOG": str(root / "skopeo.log"),
                    "PODMAN_LOG": str(podman_log),
                    "GITHUB_OUTPUT": str(output_file),
                }
            )
            image_tag = "ghcr.io/jovanille43/leos:unit-test"
            result = subprocess.run(
                ["bash", str(script), image_tag, str(authfile)],
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            repository = "ghcr.io/jovanille43/leos"
            immutable_ref = f"{repository}@{digest}"
            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                f"ref={immutable_ref}\ntag_ref={image_tag}\n",
            )
            podman_calls = podman_log.read_text(encoding="utf-8")
            self.assertIn(f"pull --authfile {authfile} {immutable_ref}", podman_calls)
            self.assertIn(f"tag {immutable_ref} {image_tag}", podman_calls)
            self.assertNotIn("inspect", podman_calls)
            self.assertIn(
                f"inspect --authfile {authfile} --format {{{{.Digest}}}} docker://{image_tag}",
                (root / "skopeo.log").read_text(encoding="utf-8"),
            )

    def test_live_image_contract_check_covers_titanoboa_inputs(self):
        checker = (ROOT / ".github/scripts/verify-live-installer-image.sh").read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for required in (
            "/usr/lib/bootc-image-builder/iso.yaml",
            "/usr/lib/modules/*/vmlinuz",
            "initramfs.img",
            "/usr/lib/grub/i386-pc/normal.mod",
            "/usr/share/grub2/unicode.pf",
            "/usr/lib/efi/shim/*/EFI/fedora",
            "mmx64.efi",
            "gcdx64.efi",
            "/boot/efi/EFI/fedora",
            "exactly one Fedora UEFI vendor directory",
            "install-image-id",
            "payload_digest",
            "payload_image_id",
            "registry_ref",
            "The embedded LEOS digest and tag references do not match.",
            "/var/lib/containers/storage",
        ):
            with self.subTest(required=required):
                self.assertIn(required, checker)
        self.assertIn("Validate Titanoboa Live image contract", workflow)
        self.assertIn("verify-live-installer-image.sh", workflow)

    def test_live_payload_is_pulled_by_digest_and_verified_after_import(self):
        containerfile = (INSTALLER / "Containerfile").read_text(encoding="utf-8")
        build_script = (INSTALLER / "src/build.sh").read_text(encoding="utf-8")
        self.assertIn("ghcr.io/ublue-os/bazzite:stable", containerfile)
        self.assertIn("INSTALL_IMAGE_REF", containerfile)
        self.assertIn("INSTALL_IMAGE_TAG_REF", containerfile)
        self.assertIn("--mount=type=secret,id=ghcr-auth", containerfile)
        self.assertIn(
            'podman pull --authfile "$REGISTRY_AUTH_FILE" "$INSTALL_IMAGE_REF"',
            build_script,
        )
        self.assertIn("skopeo inspect --authfile", build_script)
        self.assertIn("remote_digest", build_script)
        self.assertNotIn("podman image inspect --format '{{.Digest}}'", build_script)
        self.assertIn(
            'podman save --format oci-archive "$INSTALL_IMAGE_TAG_REF"',
            build_script,
        )
        self.assertIn("loaded_id", build_script)
        self.assertIn("install-image-registry-ref", build_script)
        self.assertIn("install-image-id", build_script)
        self.assertNotIn("podman images", build_script)
        self.assertIn('install -D -m 0755 "$SCRIPT_DIR/leos-root-fstab-fix.sh" /usr/share/leos-installer/leos-root-fstab-fix.sh', build_script)

    def test_anaconda_keeps_the_fedora45_compatible_install_path(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        documentation = (ROOT / "docs/titanoboa-installer.md").read_text(encoding="utf-8")
        self.assertIn("ostreecontainer --url=%s --transport=containers-storage", hook)
        self.assertIn("bootc switch --mutate-in-place --enforce-container-sigpolicy", hook)
        self.assertNotIn("bootc --source-imgref", hook)
        self.assertIn("dnf upgrade -qy anaconda-core anaconda-live anaconda-dracut", hook)
        self.assertIn("rpm -q --changelog anaconda-dracut", hook)
        self.assertIn("2332319", hook)
        self.assertIn("rootflags/fstab workaround will be applied", hook)
        self.assertNotIn("refusing to build this Live installer", hook)
        self.assertIn("leos-fstab-rootflags.ks", hook)
        self.assertIn("/usr/share/leos-installer/leos-root-fstab-fix.sh", hook)
        self.assertIn("leos-root-fstab-fix.service", hook)
        self.assertIn("graphical.target.wants", hook)
        self.assertIn("Before=graphical.target", hook)
        self.assertIn('podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -x /usr/bin/rpm-ostree', hook)
        self.assertIn("2332319", documentation)
        self.assertIn("systemd-remount-fs", documentation)

    def test_embedded_fstab_workaround_kickstart_shell_has_valid_syntax(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        marker = """cat > /usr/share/anaconda/post-scripts/leos-fstab-rootflags.ks <<'EOF'
"""
        self.assertIn(marker, hook)
        kickstart = hook.split(marker, 1)[1].split("""
EOF
""", 1)[0].splitlines()
        self.assertTrue(kickstart[0].startswith("%post --nochroot"))
        self.assertEqual(kickstart[-1], "%end")
        shell_body = "\n".join(kickstart[1:-1]) + "\n"
        result = subprocess.run(
            ["bash", "-n"],
            input=shell_body,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fstab_workaround_moves_only_root_options_to_kernel_args(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        helper = (INSTALLER / "src/leos-root-fstab-fix.sh").read_text(encoding="utf-8")
        self.assertIn("leos-fstab-rootflags.ks", hook)
        self.assertIn("graphical.target.wants", hook)
        self.assertIn('if [[ "$root_count" == "0" ]]; then', helper)
        self.assertIn('readonly rpm_ostree_bin="${LEOS_RPM_OSTREE_BIN:-rpm-ostree}"', helper)
        self.assertIn('"$rpm_ostree_bin" kargs --append-if-missing="rootflags=$rootflags"', helper)
        self.assertIn('"$rpm_ostree_bin" kargs --delete-if-present="rootflags=', helper)
        self.assertIn('fields[1] == "/"', helper)
        self.assertIn('"$systemctl_bin" reboot', helper)
        self.assertIn("Remove only the root filesystem row", helper)
        self.assertIn("rootflags=$rootflags", helper)
        self.assertNotIn("mkfs.", helper)
        self.assertNotIn("wipefs", helper)
        self.assertIn("%include /usr/share/anaconda/post-scripts/leos-fstab-rootflags.ks", hook)

    def test_root_fstab_helper_preserves_boot_esp_and_home(self):
        helper = INSTALLER / "src/leos-root-fstab-fix.sh"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = root / "run"
            run_dir.mkdir()
            fstab = root / "fstab"
            fstab.write_text(
                "# generated by Anaconda\n"
                "UUID=root / btrfs subvol=root,compress=zstd:1,ro 0 0\n"
                "UUID=boot /boot ext4 defaults 1 2\n"
                "UUID=esp /boot/efi vfat umask=0077 0 2\n"
                "UUID=home /home btrfs subvol=home,compress=zstd:1 0 0\n",
                encoding="utf-8",
            )
            rpm_log = root / "rpm-ostree.log"
            systemctl_log = root / "systemctl.log"
            rpm_ostree = root / "rpm-ostree"
            rpm_ostree.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$*\" >> \"$LEOS_TEST_RPM_LOG\"\n"
                "if [[ \"$1\" == kargs && \"$#\" -eq 1 ]]; then echo 'root=UUID=root rootflags=old'; fi\n",
                encoding="utf-8",
            )
            systemctl = root / "systemctl"
            systemctl.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\\n' \"$*\" >> \"$LEOS_TEST_SYSTEMCTL_LOG\"\n",
                encoding="utf-8",
            )
            rpm_ostree.chmod(0o755)
            systemctl.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "LEOS_ROOT_FSTAB_PATH": str(fstab),
                    "LEOS_RUN_DIR": str(run_dir),
                    "LEOS_RPM_OSTREE_BIN": str(rpm_ostree),
                    "LEOS_SYSTEMCTL_BIN": str(systemctl),
                    "LEOS_TEST_RPM_LOG": str(rpm_log),
                    "LEOS_TEST_SYSTEMCTL_LOG": str(systemctl_log),
                }
            )
            result = subprocess.run(
                ["bash", str(helper)],
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated_fstab = fstab.read_text(encoding="utf-8")
            self.assertNotIn("UUID=root / ", updated_fstab)
            self.assertIn("UUID=boot /boot ", updated_fstab)
            self.assertIn("UUID=esp /boot/efi ", updated_fstab)
            self.assertIn("UUID=home /home ", updated_fstab)

            rpm_commands = rpm_log.read_text(encoding="utf-8")
            self.assertIn("kargs --delete-if-present=rootflags=old", rpm_commands)
            self.assertIn("kargs --append-if-missing=rootflags=subvol=root,compress=zstd:1", rpm_commands)
            systemctl_commands = systemctl_log.read_text(encoding="utf-8")
            self.assertIn("disable leos-root-fstab-fix.service", systemctl_commands)
            self.assertIn("reboot", systemctl_commands)

    def test_anaconda_uses_the_embedded_image_and_preserves_existing_efi_files(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        self.assertIn("efi_dir = fedora", hook)
        self.assertIn("ostreecontainer --url=%s --transport=containers-storage", hook)
        self.assertIn(
            'bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry "$target_local_ref"',
            hook,
        )
        self.assertIn('target_cosign_key="/etc/pki/containers/leos-cosign.pub"', hook)
        self.assertIn('if [[ "$target_registry_ref" != "${target_local_ref%:*}@$target_digest" ]]; then', hook)
        self.assertIn("${target_local_ref%:*}@$target_digest", hook)
        self.assertIn(
            'podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s /etc/containers/policy.json',
            hook,
        )
        self.assertIn(
            'podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s "$target_cosign_key"',
            hook,
        )
        self.assertIn("test -s /etc/containers/registries.d/leos.yaml", hook)
        self.assertIn('boot_source="$(findmnt --raw --noheadings --output SOURCE --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"', hook)
        self.assertIn('boot_fstype="$(findmnt --raw --noheadings --output FSTYPE --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"', hook)
        self.assertIn('esp_fstype="$(findmnt --raw --noheadings --output FSTYPE --mountpoint /mnt/sysroot/boot/efi 2>/dev/null || true)"', hook)
        self.assertIn('if [[ "$esp_fstype" != "vfat" ]]; then', hook)
        self.assertIn('boot_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot/boot 2>/dev/null || true)"', hook)
        self.assertIn('root_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot 2>/dev/null || true)"', hook)
        self.assertIn('if [[ "$boot_device" == "$root_device" ]]; then', hook)
        self.assertIn('esp_device="$(findmnt --raw --noheadings --output MAJ:MIN --mountpoint /mnt/sysroot/boot/efi 2>/dev/null || true)"', hook)
        self.assertIn('if [[ "$boot_device" == "$esp_device" ]]; then', hook)
        self.assertIn('if [[ "$boot_fstype" != "ext4" ]]; then', hook)
        self.assertNotIn("e2label ", hook)
        self.assertNotIn("rm -rf /mnt/sysroot/boot/efi/EFI/fedora", hook)
        self.assertNotIn("e2label ", hook)
        self.assertNotIn("wipefs ", hook)
        self.assertNotIn("mkfs.", hook)

    def test_failure_handler_collects_anaconda_logs(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        for log_name in (
            "/tmp/anaconda.log",
            "/tmp/packaging.log",
            "/tmp/program.log",
            "/tmp/storage.log",
            "/tmp/syslog",
        ):
            self.assertIn(log_name, hook)
        self.assertIn("LEOS-installation-diagnostics.tar.gz", hook)
        self.assertIn("/tmp/leos-install-logs/*.log", hook)
        self.assertIn("journalctl -b -n 1000", hook)
        self.assertIn("%onerror", hook)

    def test_titanoboa_iso_config_has_consistent_label_and_uefi_entries(self):
        content = (INSTALLER / "src/iso.yaml").read_text(encoding="utf-8")
        self.assertIn('label: "LEOS-Live"', content)
        self.assertEqual(content.count("root=live:CDLABEL=LEOS-Live"), 2)
        self.assertIn("rd.live.image", content)
        self.assertIn("nomodeset", content)
        self.assertNotIn("  default:", content)

    def test_installed_images_require_only_leos_signed_ghcr_repositories(self):
        policy_path = ROOT / "files/leos-containers-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy["default"], [{"type": "reject"}])
        repositories = policy["transports"]["docker"]
        self.assertEqual(
            repositories[""][0]["type"], "insecureAcceptAnything"
        )
        expected = (
            "ghcr.io/jovanille43/leos",
            "ghcr.io/jovanille43/leos-nvidia",
            "ghcr.io/jovanille43/leos-nvidia-open",
        )
        for repository in expected:
            with self.subTest(repository=repository):
                rule = repositories[repository][0]
                self.assertEqual(rule["type"], "sigstoreSigned")
                self.assertEqual(
                    rule["keyPath"], "/etc/pki/containers/leos-cosign.pub"
                )
                self.assertEqual(
                    rule["signedIdentity"], {"type": "matchRepository"}
                )

        public_key = (ROOT / "files/leos-cosign.pub").read_text(encoding="utf-8")
        self.assertEqual(public_key, (ROOT / "cosign.pub").read_text(encoding="utf-8"))

        registry_config = (ROOT / "files/leos-registries.yaml").read_text(encoding="utf-8")
        self.assertEqual(registry_config.count("use-sigstore-attachments: true"), 3)

    def test_bluebuild_recipes_install_policy_public_key_and_ghcr_config(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("source: leos-containers-policy.json", recipe)
        self.assertIn("destination: /etc/containers/policy.json", recipe)
        self.assertIn("source: leos-cosign.pub", recipe)
        self.assertIn("destination: /etc/pki/containers/leos-cosign.pub", recipe)
        self.assertIn("source: leos-registries.yaml", recipe)
        self.assertIn("destination: /etc/containers/registries.d/leos.yaml", recipe)
        self.assertIn("- type: signing", recipe)

    def test_workflow_uses_pinned_titanoboa_and_checks_iso_artifacts(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "uses: ublue-os/titanoboa@5c457c3d0518bd17e754be0fd98a60d29d26abb4",
            workflow,
        )
        self.assertIn("cosign verify --key cosign.pub", workflow)
        self.assertIn("--build-arg INSTALL_IMAGE_REF=", workflow)
        self.assertIn("--build-arg INSTALL_IMAGE_TAG_REF=", workflow)
        self.assertIn("--build-arg INSTALL_IMAGE_DIGEST=", workflow)
        self.assertIn("--build-arg BASE_IMAGE=", workflow)
        self.assertIn("steps.pinned-base.outputs.ref", workflow)
        self.assertIn("skopeo inspect --authfile", workflow)
        self.assertIn("skopeo", workflow[workflow.index("Install Podman"):workflow.index("Prepare large Btrfs")])
        self.assertIn("cosign verify --key files/bazzite-cosign.pub", workflow)
        self.assertIn("--new-bundle-format=false", workflow)
        bazzite_key = (ROOT / "files/bazzite-cosign.pub").read_text(encoding="utf-8")
        self.assertIn("BEGIN PUBLIC KEY", bazzite_key)
        self.assertIn('"installer_base_image": os.environ["BASE_IMAGE_REF"]', workflow)
        self.assertIn("verify-installer-iso.sh", workflow)
        self.assertIn("sign-iso-artifacts.sh", workflow)
        self.assertNotIn("bluebuild generate-iso", workflow)

    def test_previous_iso_workflow_remains_available_for_comparison(self):
        old_workflow = ROOT / ".github/workflows/iso.yml"
        self.assertTrue(old_workflow.is_file())
        legacy_content = old_workflow.read_text(encoding="utf-8")
        self.assertIn("generate-iso", legacy_content)
        self.assertIn("blue-build/cli:v0.9-installer", legacy_content)


if __name__ == "__main__":
    unittest.main()
