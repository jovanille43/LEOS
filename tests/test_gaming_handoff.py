"""Tests for the secure Desktop-to-Gaming first-frame handshake."""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path

from launcher.handoff import (
    create_gaming_handoff_marker,
    gaming_handoff_is_ready,
    mark_gaming_handoff_ready,
    remove_gaming_handoff_marker,
)

ROOT = Path(__file__).resolve().parents[1]


class GamingHandoffMarkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.marker = create_gaming_handoff_marker()

    def tearDown(self) -> None:
        remove_gaming_handoff_marker(self.marker)

    def test_marker_is_private_and_not_ready_before_first_frame(self) -> None:
        self.assertTrue(self.marker.is_file())
        self.assertEqual(stat.S_IMODE(self.marker.stat().st_mode), 0o600)
        self.assertEqual(self.marker.stat().st_size, 0)
        self.assertFalse(gaming_handoff_is_ready(self.marker))

    def test_marker_becomes_ready_only_after_explicit_frame_acknowledgement(self) -> None:
        self.assertTrue(mark_gaming_handoff_ready(self.marker))
        self.assertTrue(gaming_handoff_is_ready(self.marker))
        self.assertEqual(self.marker.read_bytes(), b"ready\n")

    def test_marker_cannot_be_signalled_twice(self) -> None:
        self.assertTrue(mark_gaming_handoff_ready(self.marker))
        self.assertFalse(mark_gaming_handoff_ready(self.marker))

    def test_reader_rejects_unexpected_marker_contents(self) -> None:
        self.marker.write_bytes(b"launching")
        os.chmod(self.marker, 0o600)
        self.assertFalse(gaming_handoff_is_ready(self.marker))

    def test_writer_rejects_paths_outside_the_private_temp_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            foreign = Path(folder) / self.marker.name
            foreign.write_bytes(b"")
            os.chmod(foreign, 0o600)
            self.assertFalse(mark_gaming_handoff_ready(foreign))
            self.assertFalse(gaming_handoff_is_ready(foreign))

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW is unavailable")
    def test_writer_and_reader_reject_symlinked_markers(self) -> None:
        link = self.marker.with_name(self.marker.name + "-link")
        try:
            link.symlink_to(self.marker)
            self.assertFalse(mark_gaming_handoff_ready(link))
            self.assertFalse(gaming_handoff_is_ready(link))
        finally:
            link.unlink(missing_ok=True)


class GamingHandoffIntegrationTests(unittest.TestCase):
    def test_launcher_waits_for_a_frame_and_has_a_bounded_failure_path(self) -> None:
        source = (ROOT / "launcher/main.py").read_text(encoding="utf-8")
        self.assertIn("create_gaming_handoff_marker()", source)
        self.assertIn("gaming_handoff_is_ready(ready_file)", source)
        self.assertIn("time.monotonic() + 18.0", source)
        self.assertIn("QTimer.singleShot(", source)
        self.assertIn("modeLaunchFailed.emit(message)", source)

    def test_gaming_acknowledges_only_after_the_window_swaps_a_frame(self) -> None:
        source = (ROOT / "gaming/main.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.pop("LEOS_HANDOFF_READY_FILE", "")', source)
        self.assertIn("root_window.frameSwapped.connect(announce_gaming_ready)", source)
        self.assertIn("mark_gaming_handoff_ready(ready_path)", source)

    def test_selector_keeps_a_branded_cover_until_the_child_reports_failure_or_ready(self) -> None:
        source = (ROOT / "launcher/qml/ModeSelector.qml").read_text(encoding="utf-8")
        self.assertIn("id: introHandoffCrossfade", source)
        self.assertIn("id: introHandoffScreen", source)
        self.assertIn("PRÉPARATION DE VOTRE ESPACE DE JEU", source)
        self.assertIn("function onModeLaunchFailed(message)", source)
        self.assertIn("gamingHandoffPending = true", source)
        self.assertIn("introHandoffCrossfade.start()", source)


if __name__ == "__main__":
    unittest.main()
