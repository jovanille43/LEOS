"""Runtime tests for the immutable image reference helper used by the ISO workflow."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/pin-image-digest.sh"
VALID_DIGEST = "sha256:" + ("a" * 64)
VALID_IMAGES = (
    "ghcr.io/jovanille43/leos:latest",
    "ghcr.io/jovanille43/leos-nvidia:stable",
    "ghcr.io/jovanille43/leos-nvidia-open:2026.11",
)


class PinImageDigestTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.workdir = Path(self.temporary_directory.name)
        self.authfile = self.workdir / "registry-auth.json"
        self.authfile.write_text("{}", encoding="utf-8")
        self.output_file = self.workdir / "github-output.txt"
        self.call_log = self.workdir / "podman-calls.txt"
        self.fake_podman = self.workdir / "podman"
        self.fake_podman.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "printf '%s\\n' \"$*\" >> \"$PODMAN_CALL_LOG\"\n"
            "if [[ \"$1\" == pull ]]; then\n"
            "  exit \"$PODMAN_PULL_STATUS\"\n"
            "fi\n"
            "if [[ \"$1\" == image && \"$2\" == inspect ]]; then\n"
            "  printf '%s\\n' \"$PODMAN_DIGEST\"\n"
            "  exit 0\n"
            "fi\n"
            "exit 97\n",
            encoding="utf-8",
        )
        self.fake_podman.chmod(0o755)

    def run_helper(self, image_ref, *, extra_args=(), env_overrides=None):
        environment = os.environ.copy()
        environment.pop("GITHUB_OUTPUT", None)
        environment.update(
            {
                "PODMAN_BIN": str(self.fake_podman),
                "PODMAN_CALL_LOG": str(self.call_log),
                "PODMAN_DIGEST": VALID_DIGEST,
                "PODMAN_PULL_STATUS": "0",
            }
        )
        if env_overrides:
            environment.update(env_overrides)
        return subprocess.run(
            ["bash", str(SCRIPT), image_ref, str(self.authfile), *extra_args],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_pins_each_supported_image_variant_to_the_pulled_digest(self):
        for image_ref in VALID_IMAGES:
            with self.subTest(image_ref=image_ref):
                self.output_file.write_text("", encoding="utf-8")
                self.call_log.unlink(missing_ok=True)
                result = self.run_helper(
                    image_ref, extra_args=(str(self.output_file),)
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                repository = image_ref.rsplit(":", 1)[0]
                self.assertEqual(
                    self.output_file.read_text(encoding="utf-8"),
                    f"ref={repository}@{VALID_DIGEST}\n",
                )
                calls = self.call_log.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(calls), 2)
                self.assertEqual(
                    calls[0],
                    f"pull --authfile {self.authfile} {image_ref}",
                )
                self.assertEqual(
                    calls[1],
                    f"image inspect --format {{{{.Digest}}}} {image_ref}",
                )

    def test_rejects_untrusted_repositories_and_unexpected_image_names(self):
        invalid_refs = (
            "ghcr.io/attacker/leos:latest",
            "ghcr.io/jovanille43/other-image:latest",
            "docker.io/jovanille43/leos:latest",
            "ghcr.io/jovanille43/leos:latest;touch /tmp/unexpected",
        )
        for image_ref in invalid_refs:
            with self.subTest(image_ref=image_ref):
                result = self.run_helper(
                    image_ref, extra_args=(str(self.output_file),)
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.call_log.exists())
                self.assertFalse(self.output_file.exists())

    def test_refuses_to_continue_without_registry_auth_file(self):
        self.authfile.unlink()
        result = self.run_helper(
            VALID_IMAGES[0], extra_args=(str(self.output_file),)
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.call_log.exists())
        self.assertFalse(self.output_file.exists())

    def test_requires_an_output_destination_before_pulling(self):
        result = self.run_helper(VALID_IMAGES[0])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.call_log.exists())

    def test_rejects_a_missing_or_malformed_digest(self):
        for digest in ("", "latest", "sha256:abc", "sha256:" + ("A" * 64)):
            with self.subTest(digest=digest):
                self.call_log.unlink(missing_ok=True)
                result = self.run_helper(
                    VALID_IMAGES[0],
                    extra_args=(str(self.output_file),),
                    env_overrides={"PODMAN_DIGEST": digest},
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.output_file.exists())
                calls = self.call_log.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(calls), 2)

    def test_propagates_registry_pull_failure_without_writing_output(self):
        result = self.run_helper(
            VALID_IMAGES[0],
            extra_args=(str(self.output_file),),
            env_overrides={"PODMAN_PULL_STATUS": "23"},
        )
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.output_file.exists())
        self.assertEqual(
            self.call_log.read_text(encoding="utf-8").splitlines(),
            [f"pull --authfile {self.authfile} {VALID_IMAGES[0]}"],
        )


if __name__ == "__main__":
    unittest.main()
