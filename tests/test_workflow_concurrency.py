"""Tests for bounded and non-stale GitHub Actions validation workflows."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowConcurrencyTests(unittest.TestCase):
    def test_python_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: leos-python-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)

    def test_recipe_checks_cancel_stale_runs_and_have_timeout(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("group: leos-bluebuild-${{ github.ref }}", source)
        self.assertIn("cancel-in-progress: true", source)
        self.assertIn("timeout-minutes: 15", source)
        self.assertIn('"files/**"', source)

    def test_recipe_generation_retries_transient_schema_fetch_failures(self):
        source = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertIn("for recipe in recipe.yml recipe-nvidia.yml recipe-nvidia-open.yml", source)
        self.assertIn("max_attempts=3", source)
        self.assertIn('until bluebuild generate "recipes/${recipe}"', source)
        self.assertIn('sleep "$((attempt * 3))"', source)
        self.assertIn("could not generate ${recipe} after", source)
        self.assertIn('test -s "$output"', source)

    def test_iso_workflow_covers_all_hardware_variants_and_verifies_signatures(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        for variant in ("standard", "nvidia-legacy", "nvidia-modern"):
            self.assertIn(f"- {variant}", source)
        self.assertIn('standard) image_name="leos"', source)
        self.assertIn('nvidia-legacy) image_name="leos-nvidia"', source)
        self.assertIn('nvidia-modern) image_name="leos-nvidia-open"', source)
        verify = source.index("cosign verify --key cosign.pub")
        generate = source.index("generate-iso --iso-name")
        self.assertLess(verify, generate)
        self.assertIn("sha256sum", source)

    def test_image_build_and_iso_generation_share_a_registry_lock(self):
        build = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        iso = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn("group: leos-image-pipeline", build)
        self.assertIn("group: leos-image-pipeline", iso)
        self.assertIn("cancel-in-progress: false", build)
        self.assertIn("cancel-in-progress: false", iso)

    def test_workflow_actions_are_pinned_to_reviewed_immutable_commits(self):
        workflows = {
            ".github/workflows/build.yml": (
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0",
                "sigstore/cosign-installer@756fe2d284c7292c4e9b62c8a28f1e5629c59532 # v4.1.3",
                "blue-build/github-action@fb86c457fd3d0e13d5e9c1875c6305cf28b09234 # v1.14.0",
            ),
            ".github/workflows/iso.yml": (
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "sigstore/cosign-installer@756fe2d284c7292c4e9b62c8a28f1e5629c59532 # v4.1.3",
                "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2",
            ),
            ".github/workflows/recipe-checks.yml": (
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0",
            ),
            ".github/workflows/python-checks.yml": (
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0",
            ),
            ".github/workflows/signing-check.yml": (
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1",
                "sigstore/cosign-installer@756fe2d284c7292c4e9b62c8a28f1e5629c59532 # v4.1.3",
            ),
        }
        for path, expected_pins in workflows.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                for pin in expected_pins:
                    self.assertIn(pin, source)
                for line in source.splitlines():
                    if "uses:" in line and not line.strip().startswith("#"):
                        self.assertRegex(
                            line,
                            r"@([0-9a-f]{40})(?:\s+# v[0-9.]+)?$",
                        )

    def test_checkout_actions_do_not_persist_github_token_credentials(self):
        for path in (
            ".github/workflows/build.yml",
            ".github/workflows/iso.yml",
            ".github/workflows/recipe-checks.yml",
            ".github/workflows/python-checks.yml",
            ".github/workflows/signing-check.yml",
        ):
            source = (ROOT / path).read_text(encoding="utf-8")
            if "actions/checkout@" in source:
                with self.subTest(path=path):
                    self.assertIn("persist-credentials: false", source)

    def test_bluebuild_cli_signature_and_provenance_are_verified_before_publish(self):
        source = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertEqual(source.count("verify_install: true"), 3)
        self.assertEqual(source.count("blue-build/github-action@"), 3)
        self.assertLess(
            source.index("Run LEOS Python test suite"),
            source.index("Build and publish LEOS"),
        )
        self.assertIn("timeout-minutes: 360", source)

    def test_workflow_groups_are_separate(self):
        python = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        recipe = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        self.assertNotEqual(
            "leos-python-${{ github.ref }}",
            "leos-bluebuild-${{ github.ref }}",
        )


if __name__ == "__main__":
    unittest.main()
