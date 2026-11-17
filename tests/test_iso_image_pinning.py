"""Tests for immutable GHCR image references used by ISO generation."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/pin-image-digest.sh"
VALID_IMAGE = "ghcr.io/leos-owner/leos:latest"
VALID_DIGEST = "sha256:" + "a" * 64


class IsoImagePinningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.authfile = self.root / "auth.json"
        self.authfile.write_text("{}", encoding="utf-8")
        self.output_file = self.root / "github-output"
        self.podman_log = self.root / "podman-calls"
        self.skopeo_log = self.root / "skopeo-calls"

        self.skopeo = self.root / "skopeo"
        self.skopeo.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$*\" >> \"$SKOPEO_CALL_LOG\"\n"
            "if [[ \"$1\" == inspect ]]; then\n"
            "  if [[ \"$SKOPEO_EXIT\" != 0 ]]; then exit \"$SKOPEO_EXIT\"; fi\n"
            "  printf '%s\\n' \"$MOCK_DIGEST\"\n"
            "  exit 0\n"
            "fi\n"
            "exit 64\n",
            encoding="utf-8",
        )
        self.podman = self.root / "podman"
        self.podman.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$*\" >> \"$PODMAN_CALL_LOG\"\n"
            "if [[ \"$1\" == pull ]]; then exit \"$MOCK_PULL_EXIT\"; fi\n"
            "if [[ \"$1\" == tag ]]; then exit 0; fi\n"
            "exit 64\n",
            encoding="utf-8",
        )
        self.skopeo.chmod(0o755)
        self.podman.chmod(0o755)

    def run_helper(self, image_ref=VALID_IMAGE, *, digest=VALID_DIGEST, pull_exit=0, skopeo_exit=0):
        environment = os.environ.copy()
        environment.update(
            {
                "PODMAN_BIN": str(self.podman),
                "PODMAN_CALL_LOG": str(self.podman_log),
                "MOCK_PULL_EXIT": str(pull_exit),
                "SKOPEO_BIN": str(self.skopeo),
                "SKOPEO_CALL_LOG": str(self.skopeo_log),
                "MOCK_DIGEST": digest,
                "SKOPEO_EXIT": str(skopeo_exit),
            }
        )
        return subprocess.run(
            ["bash", str(SCRIPT), image_ref, str(self.authfile), str(self.output_file)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_resolves_registry_digest_then_pulls_immutable_reference(self):
        result = self.run_helper()

        self.assertEqual(result.returncode, 0, result.stderr)
        repository = "ghcr.io/leos-owner/leos"
        immutable_ref = f"{repository}@{VALID_DIGEST}"
        self.assertEqual(
            self.output_file.read_text(encoding="utf-8"),
            f"ref={immutable_ref}\n"
            f"tag_ref={VALID_IMAGE}\n",
        )
        self.assertEqual(
            self.podman_log.read_text(encoding="utf-8").splitlines(),
            [
                f"pull --authfile {self.authfile} {immutable_ref}",
                f"tag {immutable_ref} {VALID_IMAGE}",
            ],
        )
        self.assertEqual(
            self.skopeo_log.read_text(encoding="utf-8").splitlines(),
            [
                f"inspect --authfile {self.authfile} --format {{{{.Digest}}}} docker://{VALID_IMAGE}"
            ],
        )

    def test_rejects_image_references_outside_the_expected_ghcr_names(self):
        for image_ref in (
            "docker.io/leos-owner/leos:latest",
            "ghcr.io/leos-owner/unrelated:latest",
            "ghcr.io/leos-owner/leos:latest;touch /tmp/unexpected",
            "ghcr.io/leos-owner/leos",
        ):
            with self.subTest(image_ref=image_ref):
                result = self.run_helper(image_ref)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.skopeo_log.exists())
                self.assertFalse(self.podman_log.exists())
                self.assertFalse(self.output_file.exists())

    def test_rejects_malformed_registry_digest_without_writing_output(self):
        result = self.run_helper(digest="not-a-digest")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valid top-level SHA-256 manifest digest", result.stderr)
        self.assertFalse(self.output_file.exists())
        self.assertFalse(self.podman_log.exists())

    def test_skopeo_resolution_failure_does_not_pull_or_pin_image(self):
        result = self.run_helper(skopeo_exit=23)

        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.output_file.exists())
        self.assertFalse(self.podman_log.exists())
        self.assertEqual(len(self.skopeo_log.read_text(encoding="utf-8").splitlines()), 1)

    def test_immutable_podman_pull_failure_does_not_write_output(self):
        result = self.run_helper(pull_exit=23)

        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.output_file.exists())
        repository = "ghcr.io/leos-owner/leos"
        self.assertEqual(
            self.podman_log.read_text(encoding="utf-8").splitlines(),
            [f"pull --authfile {self.authfile} {repository}@{VALID_DIGEST}"],
        )

    def test_missing_authfile_fails_before_skopeo_or_podman(self):
        self.authfile.unlink()
        result = self.run_helper()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("auth file is missing", result.stdout)
        self.assertFalse(self.skopeo_log.exists())
        self.assertFalse(self.podman_log.exists())
        self.assertFalse(self.output_file.exists())

    def test_requires_output_destination_before_resolving_or_pulling(self):
        environment = os.environ.copy()
        environment.update(
            {
                "PODMAN_BIN": str(self.podman),
                "PODMAN_CALL_LOG": str(self.podman_log),
                "SKOPEO_BIN": str(self.skopeo),
                "SKOPEO_CALL_LOG": str(self.skopeo_log),
                "MOCK_DIGEST": VALID_DIGEST,
                "MOCK_PULL_EXIT": "0",
                "SKOPEO_EXIT": "0",
            }
        )
        result = subprocess.run(
            ["bash", str(SCRIPT), VALID_IMAGE, str(self.authfile)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.skopeo_log.exists())
        self.assertFalse(self.podman_log.exists())


if __name__ == "__main__":
    unittest.main()
