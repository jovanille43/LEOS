"""Tests that lightweight LEOS applications skip intro-video re-encoding."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop.branding_assets import build_themed_branding_assets, source_asset_urls


class ThemeControllerAssetBudgetTests(unittest.TestCase):
    def test_lightweight_asset_build_does_not_reencode_intro_videos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "branding"
            (root / "wallpapers").mkdir(parents=True)
            (root / "animations").mkdir()
            for relative in (
                "desktop-logo.jpeg", "gaming-logo.jpeg",
                "wallpapers/desktop-leos.svg", "wallpapers/gaming-leos.svg",
                "animations/desktop-intro.mov", "animations/gaming-intro.mp4",
            ):
                (root / relative).write_bytes(b"source asset")
            cache = Path(directory) / "cache"
            with patch.dict(os.environ, {"XDG_CACHE_HOME": str(cache)}):
                with (
                    patch("desktop.branding_assets._image_transform", return_value=False),
                    patch("desktop.branding_assets._transform_svg", return_value=False),
                    patch("desktop.branding_assets._transform_video") as encode_video,
                ):
                    urls = build_themed_branding_assets(
                        "#FF8800", "#0055CC", root, generate_videos=False
                    )
                encode_video.assert_not_called()
                original = source_asset_urls(root)
                self.assertEqual(urls["desktopIntroUrl"], original["desktopIntroUrl"])
                self.assertEqual(urls["gamingIntroUrl"], original["gamingIntroUrl"])


if __name__ == "__main__":
    unittest.main()
