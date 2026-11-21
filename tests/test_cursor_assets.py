"""Behavioral tests for the generated LEOS SVG cursor family."""

import json
import os
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "files" / "scripts" / "prepare-leos-cursors.sh"
EXPECTED = {
    "pointer": (8, 7),
    "text": (16, 16),
    "wait": (16, 16),
    "progress": (4, 3),
    "crosshair": (16, 16),
    "not-allowed": (16, 16),
    "move": (16, 16),
    "ew-resize": (16, 16),
    "ns-resize": (16, 16),
    "nwse-resize": (16, 16),
    "nesw-resize": (16, 16),
}


class LeosCursorAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name) / "icons" / "leos" / "cursors_scalable"

    def tearDown(self):
        self.temp.cleanup()

    def run_generator(self):
        environment = dict(os.environ)
        environment["LEOS_CURSOR_THEME_ROOT"] = str(self.output)
        return subprocess.run(
            ["bash", str(SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env=environment,
        )

    def test_generates_complete_svg_cursor_family_with_valid_hotspots(self):
        result = self.run_generator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Generated {len(EXPECTED)} LEOS scalable cursor shapes", result.stdout)

        generated = {path.name for path in self.output.iterdir() if path.is_dir()}
        self.assertEqual(generated, set(EXPECTED))

        for name, hotspot in EXPECTED.items():
            with self.subTest(cursor=name):
                directory = self.output / name
                metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
                self.assertEqual(len(metadata), 1)
                self.assertEqual(metadata[0]["filename"], f"{name}.svg")
                self.assertEqual(
                    (metadata[0]["hotspot_x"], metadata[0]["hotspot_y"]),
                    hotspot,
                )
                self.assertEqual(metadata[0]["nominal_size"], 32)

                root = ET.parse(directory / f"{name}.svg").getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                accents = [
                    item.attrib["stop-color"]
                    for item in root.iter()
                    if "stop-color" in item.attrib
                ]
                self.assertEqual(accents, ["#00D9FF", "#E33BFF"])

    def test_generation_is_repeatable_and_keeps_each_shape_in_its_directory(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = {
            path.relative_to(self.output).as_posix(): path.read_bytes()
            for path in self.output.rglob("*")
            if path.is_file()
        }
        second = self.run_generator()
        self.assertEqual(second.returncode, 0, second.stderr)
        after = {
            path.relative_to(self.output).as_posix(): path.read_bytes()
            for path in self.output.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)

    def test_generator_refuses_a_symlink_output_root(self):
        target = Path(self.temp.name) / "real"
        target.mkdir()
        self.output.parent.mkdir(parents=True)
        self.output.symlink_to(target, target_is_directory=True)
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stderr.lower())
        self.assertEqual(list(target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
