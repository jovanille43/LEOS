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
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    ["bash", "-n", str(script)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_live_payload_is_pulled_by_digest_and_verified_after_import(self):
        containerfile = (INSTALLER / "Containerfile").read_text(encoding="utf-8")
        build_script = (INSTALLER / "src/build.sh").read_text(encoding="utf-8")
        self.assertIn("ghcr.io/ublue-os/bazzite:stable", containerfile)
        self.assertIn("INSTALL_IMAGE_REF", containerfile)
        self.assertIn("INSTALL_IMAGE_TAG_REF", containerfile)
        self.assertIn("--mount=type=secret,id=ghcr-auth", containerfile)
        self.assertIn('podman pull --authfile "$REGISTRY_AUTH_FILE" "$INSTALL_IMAGE_REF"', build_script)
        self.assertIn("podman image inspect --format '{{.Digest}}'", build_script)
        self.assertIn('podman save --format oci-archive "$INSTALL_IMAGE_TAG_REF"', build_script)
        self.assertIn("loaded_id", build_script)
        self.assertIn("install-image-registry-ref", build_script)
        self.assertIn("install-image-id", build_script)
        self.assertNotIn("podman images", build_script)

    def test_anaconda_uses_the_exact_image_and_separate_efi_directory(self):
        hook = (INSTALLER / "src/titanoboa_hook_postrootfs.sh").read_text(encoding="utf-8")
        self.assertIn("efi_dir = leos", hook)
        self.assertIn("ostreecontainer --url=%s --transport=containers-storage", hook)
        self.assertIn(
            'bootc switch --mutate-in-place --enforce-container-sigpolicy --transport registry "$target_registry_ref"',
            hook,
        )
        self.assertIn(
            'podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s /etc/containers/policy.json',
            hook,
        )
        self.assertIn(
            'podman run --rm --network=none --entrypoint /usr/bin/test "$target_local_ref" -s /etc/pki/containers/leos-cosign.pub',
            hook,
        )
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
        self.assertIn("%onerror", hook)

    def test_titanoboa_iso_config_has_consistent_label_and_uefi_entries(self):
        content = (INSTALLER / "src/iso.yaml").read_text(encoding="utf-8")
        self.assertIn('label: "LEOS-Live"', content)
        self.assertEqual(content.count("root=live:CDLABEL=LEOS-Live"), 2)
        self.assertIn("rd.live.image", content)
        self.assertIn("nomodeset", content)

    def test_installed_images_require_leos_signatures_without_blocking_other_registries(self):
        policy_path = ROOT / "files/leos-containers-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(policy["default"], [{"type": "insecureAcceptAnything"}])
        docker = policy["transports"]["docker"]
        expected = (
            "ghcr.io/jovanille43/leos",
            "ghcr.io/jovanille43/leos-nvidia",
            "ghcr.io/jovanille43/leos-nvidia-open",
        )
        for repository in expected:
            with self.subTest(repository=repository):
                rules = docker[repository]
                self.assertEqual(len(rules), 1)
                self.assertEqual(rules[0]["type"], "sigstoreSigned")
                self.assertEqual(
                    rules[0]["keyPath"], "/etc/pki/containers/leos-cosign.pub"
                )
                self.assertEqual(
                    rules[0]["signedIdentity"], {"type": "matchRepository"}
                )
        public_key = (ROOT / "files/leos-cosign.pub").read_text(encoding="utf-8")
        self.assertIn("BEGIN PUBLIC KEY", public_key)

    def test_bluebuild_recipe_installs_signature_policy_and_public_key(self):
        recipe = (ROOT / "recipes/common-modules.yml").read_text(encoding="utf-8")
        self.assertIn("source: leos-containers-policy.json", recipe)
        self.assertIn("destination: /etc/containers/policy.json", recipe)
        self.assertIn("source: leos-cosign.pub", recipe)
        self.assertIn("destination: /etc/pki/containers/leos-cosign.pub", recipe)

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
        self.assertIn("verify-installer-iso.sh", workflow)
        self.assertIn("sign-iso-artifacts.sh", workflow)
        self.assertNotIn("bluebuild generate-iso", workflow)

    def test_previous_iso_workflow_remains_available_for_comparison(self):
        old_workflow = ROOT / ".github/workflows/iso.yml"
        self.assertTrue(old_workflow.is_file())
        self.assertIn(
            "bluebuild generate-iso",
            old_workflow.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
