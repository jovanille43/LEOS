"""Tests for bounded and non-stale GitHub Actions validation workflows."""

from pathlib import Path
import re
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

    def test_iso_workflow_pins_one_digest_before_signature_verification(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        login = source.index("Authenticate to GitHub Container Registry")
        pin = source.index("Resolve and pin the published image digest")
        verify = source.index("Verify published LEOS image signature")
        generate = source.index("Generate bootable installer ISO")
        self.assertLess(login, pin)
        self.assertLess(pin, verify)
        self.assertLess(verify, generate)
        self.assertIn("id: pinned-image", source[pin:verify])
        self.assertIn("bash .github/scripts/pin-image-digest.sh", source[pin:verify])
        self.assertIn("IMAGE_REF: ${{ steps.pinned-image.outputs.ref }}", source[verify:generate])
        self.assertIn("IMAGE_REF: ${{ steps.pinned-image.outputs.ref }}", source[generate:])
        self.assertNotIn("steps.image.outputs.ref", source[verify:])

    def test_iso_digest_pinning_helper_validates_and_emits_sha256_reference(self):
        helper = (ROOT / ".github/scripts/pin-image-digest.sh").read_text(encoding="utf-8")
        self.assertIn('podman_bin="${PODMAN_BIN:-podman}"', helper)
        self.assertIn('pull --authfile "$authfile" "$image_ref"', helper)
        self.assertIn("image inspect --format '{{.Digest}}'", helper)
        self.assertIn(r"^sha256:[0-9a-f]{64}$", helper)
        self.assertIn(r"printf 'ref=%s@%s\n'", helper)
        self.assertIn("leos-nvidia-open", helper)


    def test_iso_artifacts_include_a_source_and_checksum_provenance_manifest(self):
        source = (ROOT / ".github/workflows/iso.yml").read_text(encoding="utf-8")
        self.assertIn('echo "provenance=LEOS-$VARIANT-$IMAGE_TAG.iso.json"', source)
        self.assertIn("MANIFEST_NAME:", source)
        self.assertIn('"source_image": os.environ["IMAGE_REF"]', source)
        self.assertIn('"iso_sha256": os.environ["ISO_SHA256"]', source)
        self.assertIn('"source_commit": os.environ["GITHUB_SHA"]', source)
        self.assertIn('"workflow_run_id": int(os.environ["GITHUB_RUN_ID"])', source)
        self.assertIn('sha256sum --check "$ISO_NAME.sha256"', source)
        self.assertIn("steps.image.outputs.provenance", source)

    def test_workflow_groups_are_separate(self):
        python = (ROOT / ".github/workflows/python-checks.yml").read_text(encoding="utf-8")
        recipe = (ROOT / ".github/workflows/recipe-checks.yml").read_text(encoding="utf-8")
        group = re.compile(r"^\s+group:\s*(\S+)", re.M)
        python_group = group.search(python)
        recipe_group = group.search(recipe)
        self.assertIsNotNone(python_group)
        self.assertIsNotNone(recipe_group)
        self.assertNotEqual(python_group.group(1), recipe_group.group(1))


if __name__ == "__main__":
    unittest.main()
