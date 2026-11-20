"""Tests that lightweight LEOS windows do not re-encode intro videos."""

import unittest
from unittest.mock import patch

from desktop.theme_controller import _BrandingAssetTask


class ThemeControllerAssetBudgetTests(unittest.TestCase):
    def test_lightweight_asset_task_disables_video_generation(self):
        snapshot = ("#FF8800", "#0055CC")
        task = _BrandingAssetTask(snapshot, generate_videos=False)
        with patch("desktop.theme_controller.build_themed_branding_assets", return_value={}) as build:
            task.run()
        build.assert_called_once_with(*snapshot, generate_videos=False)

    def test_full_asset_task_keeps_video_generation_enabled(self):
        snapshot = ("#FF8800", "#0055CC")
        task = _BrandingAssetTask(snapshot)
        with patch("desktop.theme_controller.build_themed_branding_assets", return_value={}) as build:
            task.run()
        build.assert_called_once_with(*snapshot, generate_videos=True)


if __name__ == "__main__":
    unittest.main()
