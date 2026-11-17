"""Contract tests for the Titanoboa-based LEOS installer pipeline."""

import json
from pathlib import Path
import subprocess
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
            ROOT / ".github/scripts/verify-live-installer-image.sh",
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
        self.assertIn("podman image inspect --format '{{.Digest}}'", build_script)
        self.assertIn(
            'podman save --format oci-archive "$INSTALL_IMAGE_TAG_REF"',
            build_script,
        )
        self.assertIn("loaded_id", build_script)
        self.assertIn("install-image-registry-ref", build_script)
        self.assertIn("install-image-id", build_script)
        self.assertNotIn("podman images", build_script)

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
        self.assertIn('rpm-ostree kargs --append-if-missing="rootflags=$rootflags"', hook)
        self.assertIn('rootflags_file=/run/leos-rootflags', hook)
        self.assertIn("2332319", documentation)
        self.assertIn("systemd-remount-fs", documentation)

    def test_fstab_workaround_moves_only_root_options_to_kernel_args(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        self.assertIn("leos-fstab-rootflags.ks", hook)
        self.assertIn('rootflags="$(< "$rootflags_file")"', hook)
        self.assertIn('rpm-ostree kargs --append-if-missing="rootflags=$rootflags"', hook)
        self.assertIn("Moved root mount options to the kernel command line", hook)
        self.assertIn("Remove only the root filesystem line", hook)
        self.assertIn("root fstab row", hook)
        self.assertIn("%include /usr/share/anaconda/post-scripts/leos-fstab-rootflags.ks", hook)

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
        self.assertIn('live_digest="$(podman image inspect --format', hook)
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
