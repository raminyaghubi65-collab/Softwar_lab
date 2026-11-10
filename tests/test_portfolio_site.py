import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "index.html"


class PortfolioHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.stylesheets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.stylesheets.append(attrs.get("href"))


class PortfolioSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = SITE.read_text(encoding="utf-8")
        cls.parser = PortfolioHTMLParser()
        cls.parser.feed(cls.html)
        cls.parser.close()

    def test_html_has_mobile_viewport_and_language(self):
        self.assertIn('<html lang="en">', self.html)
        self.assertIn('name="viewport"', self.html)

    def test_internal_navigation_targets_exist(self):
        ids = self.parser.ids
        self.assertEqual(len(ids), len(set(ids)), "HTML IDs must be unique")
        for href in self.parser.links:
            if href.startswith("#"):
                self.assertIn(href[1:], ids, f"Missing anchor target: {href}")

    def test_local_stylesheet_exists(self):
        self.assertIn("style.css", self.parser.stylesheets)
        for href in self.parser.stylesheets:
            self.assertTrue((SITE.parent / href).is_file(), f"Missing stylesheet: {href}")

    def test_contact_does_not_send_private_details_to_public_issue(self):
        self.assertNotIn("/issues/new", self.html)
        self.assertIn("github.com/raminyaghubi65-collab", self.html)
        self.assertIn("Do not post private staging links", self.html)


if __name__ == "__main__":
    unittest.main()
