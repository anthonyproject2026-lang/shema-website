import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SCRIPT = ROOT / "script.js"
HEADERS = ROOT / "_headers"
ROBOTS = ROOT / "robots.txt"

FACEBOOK_LINKS = {
    "Voice of Vineeth Sreenivasan Live": "https://www.facebook.com/share/v/1c8QmG9wZi/",
    "Talent Show 2K26": "https://www.facebook.com/reel/1500400011768100",
    "Onam Core Committee 2K26": "https://www.facebook.com/reel/1581554060224328",
    "Onam Celebration 2K26": "https://www.facebook.com/reel/1132441579444104",
    "Onanilavu 2K26": "https://www.facebook.com/reel/1578855873677593",
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))


class ShemaSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.headers = HEADERS.read_text(encoding="utf-8")
        cls.robots = ROBOTS.read_text(encoding="utf-8")
        cls.links = LinkParser()
        cls.links.feed(cls.html)

    def test_prime_events_section_replaces_upcoming_events(self):
        self.assertIn("Prime Events of the Year", self.html)
        self.assertIn("Moments to Remember", self.html)
        self.assertNotIn("Upcoming Events", self.html)
        self.assertNotIn("Previous Events", self.html)

    def test_all_five_requested_events_are_present(self):
        for title in FACEBOOK_LINKS:
            with self.subTest(title=title):
                self.assertIn(title, self.html)

    def test_prime_events_lists_exactly_five_cards(self):
        marker = 'class="event-card event-memory-card reveal"'
        self.assertEqual(self.html.count(marker), 5)

    def test_all_facebook_links_are_safe_external_links(self):
        links_by_href = {link.get("href"): link for link in self.links.links}
        for title, url in FACEBOOK_LINKS.items():
            with self.subTest(title=title):
                self.assertIn(url, links_by_href)
                link = links_by_href[url]
                self.assertEqual("_blank", link.get("target"))
                rel = set((link.get("rel") or "").split())
                self.assertTrue({"noopener", "noreferrer"}.issubset(rel))

    def test_facebook_is_not_embedded_or_loaded_as_a_script(self):
        self.assertNotRegex(self.html, r"<iframe[^>]+facebook\.com")
        self.assertNotRegex(self.html, r"<script[^>]+facebook\.com")

    def test_voice_event_has_local_photo_gallery_hook(self):
        self.assertRegex(
            self.html,
            r'data-event-gallery="voice-vineeth"',
        )
        self.assertIn('id="eventGalleryModal"', self.html)
        self.assertIn('id="eventGalleryClose"', self.html)
        self.assertIn("setupEventGallery", self.script)

    def test_historical_leadership_section_is_present(self):
        self.assertIn("Leadership Through the Years", self.html)
        self.assertIn(
            "Celebrating a Decade of Service, Dedication &amp; Community Leadership",
            self.html,
        )

    def test_unsecured_admin_panel_is_not_deployed(self):
        for filename in ("admin.html", "admin.css", "admin.js"):
            with self.subTest(filename=filename):
                self.assertFalse((ROOT / filename).exists())
        self.assertNotIn("shema_admin_", self.script)
        self.assertNotIn("localStorage", self.script)

    def test_robots_file_has_no_stale_admin_reference(self):
        self.assertNotIn("/admin", self.robots)

    def test_static_leadership_copy_is_not_a_live_status(self):
        self.assertNotIn('leadership-placeholder reveal" role="status', self.html)

    def test_security_headers_remain_restrictive(self):
        self.assertIn("X-Frame-Options: DENY", self.headers)
        self.assertIn("X-Content-Type-Options: nosniff", self.headers)
        self.assertIn("script-src 'self'", self.headers)
        self.assertNotIn("facebook.com", self.headers)

    def test_no_blank_external_link_lacks_noopener(self):
        for link in self.links.links:
            if link.get("target") == "_blank":
                rel = set((link.get("rel") or "").split())
                self.assertIn("noopener", rel, link.get("href"))
                self.assertIn("noreferrer", rel, link.get("href"))


if __name__ == "__main__":
    unittest.main()
