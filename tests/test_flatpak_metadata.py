"""Tests for safe display of Flatpak runtime metadata."""

import unittest

from shop.flatpak_metadata import application_runtime, runtime_summary


class FlatpakMetadataTests(unittest.TestCase):
    def test_reads_runtime_from_application_section(self):
        metadata = (
            "[Application]\n"
            "name=org.example.App\n"
            "runtime=org.freedesktop.Platform/x86_64/24.08\n"
            "sdk=org.freedesktop.Sdk/x86_64/24.08\n"
        )
        self.assertEqual(
            application_runtime(metadata),
            "org.freedesktop.Platform/x86_64/24.08",
        )

    def test_ignores_runtime_values_outside_application_section(self):
        metadata = (
            "[Extension org.example.Extension]\n"
            "runtime=org.example.Wrong/x86_64/stable\n"
            "[Application]\n"
            "name=org.example.App\n"
        )
        self.assertEqual(application_runtime(metadata), "")

    def test_rejects_malformed_runtime_ref(self):
        self.assertEqual(
            application_runtime("[Application]\nruntime=bad ref\n"),
            "",
        )

    def test_summary_does_not_claim_unknown_dependencies(self):
        summary = runtime_summary("[Application]\nname=org.example.App\n")
        self.assertIn("Aucun runtime explicite", summary)
        self.assertIn("Flatpak résoudra les dépendances", summary)

    def test_summary_names_declared_runtime(self):
        summary = runtime_summary(
            "[Application]\nruntime=org.freedesktop.Platform/x86_64/24.08\n"
        )
        self.assertIn("org.freedesktop.Platform/x86_64/24.08", summary)
        self.assertIn("si besoin", summary)


if __name__ == "__main__":
    unittest.main()
