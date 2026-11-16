from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.fragments: list[str] = []
        self.local_paths: list[str] = []
        self.images_without_alt: list[str] = []
        self.download_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.append(element_id)

        href = values.get("href")
        if href:
            parsed = urlparse(href)
            if href.startswith("#") and len(href) > 1:
                self.fragments.append(href[1:])
            elif not parsed.scheme and not href.startswith(("/", "//")):
                path = parsed.path
                if path:
                    self.local_paths.append(path)

        src = values.get("src")
        if src:
            parsed = urlparse(src)
            if not parsed.scheme and not src.startswith(("/", "//")):
                self.local_paths.append(parsed.path)

        if tag == "img" and "alt" not in values:
            self.images_without_alt.append(values.get("src", "<image sans source>"))

        if tag in {"a", "button"} and (
            "download" in values or (href and ".iso" in href.lower())
        ):
            self.download_links.append(href or values.get("download", "download"))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


class WebsiteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HTML_FILE.read_text(encoding="utf-8")
        cls.parser = SiteParser()
        cls.parser.feed(cls.source)
        cls.parser.close()

    def test_required_sections_exist(self) -> None:
        expected = {
            "accueil",
            "experience",
            "editions",
            "compatibilite",
            "securite",
            "telechargement",
        }
        self.assertTrue(expected.issubset(set(self.parser.ids)))

    def test_ids_are_unique(self) -> None:
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))

    def test_document_has_language_and_metadata(self) -> None:
        self.assertIn('<html lang="fr">', self.source)
        self.assertIn('<meta name="viewport"', self.source)
        self.assertIn('<meta name="description"', self.source)

    def test_fragment_links_resolve(self) -> None:
        missing = sorted(set(self.parser.fragments) - set(self.parser.ids))
        self.assertEqual(missing, [])

    def test_local_assets_exist(self) -> None:
        missing = [
            path for path in self.parser.local_paths
            if not (ROOT / path).is_file()
        ]
        self.assertEqual(missing, [])

    def test_images_have_alt_attributes(self) -> None:
        self.assertEqual(self.parser.images_without_alt, [])

    def test_no_iso_download_is_advertised_before_release(self) -> None:
        self.assertEqual(self.parser.download_links, [])
        self.assertIn("Aucune version publiée", self.source)
        self.assertIn("disabled", self.source)


    def test_theme_controls_are_present(self) -> None:
        for marker in (
            'id="theme-toggle"',
            'id="theme-panel"',
            'data-theme-mode="dark"',
            'data-theme-mode="light"',
            'data-theme-mode="auto"',
            'id="theme-color-a"',
            'id="theme-color-b"',
            'id="theme-reset"',
        ):
            self.assertIn(marker, self.source)

    def test_site_uses_the_same_leos_default_colors(self) -> None:
        self.assertIn('value="#00D9FF"', self.source)
        self.assertIn('value="#E33BFF"', self.source)
        script = (ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn('colorA: "#00D9FF"', script)
        self.assertIn('colorB: "#E33BFF"', script)

    def test_theme_auto_schedule_matches_leos(self) -> None:
        script = (ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn('hour >= 7 && hour < 19', script)
        self.assertIn('next.setHours(19, 0, 0, 0)', script)
        self.assertIn('next.setHours(7, 0, 0, 0)', script)

    def test_user_colors_drive_the_gradient(self) -> None:
        script = (ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn('root.style.setProperty("--a", preferences.colorA)', script)
        self.assertIn('root.style.setProperty("--b", preferences.colorB)', script)
        self.assertIn('localStorage.setItem(STORAGE_KEY', script)



    def test_logos_are_recolored_from_the_selected_pair(self) -> None:
        self.assertGreaterEqual(self.source.count("data-themeable-logo"), 2)
        script = (ROOT / "script.js").read_text(encoding="utf-8")
        self.assertIn("function recolorBrandingLogos()", script)
        self.assertIn("source lightness", script.lower())



if __name__ == "__main__":
    unittest.main()
