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
        self._inside_image = False

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


if __name__ == "__main__":
    unittest.main()
