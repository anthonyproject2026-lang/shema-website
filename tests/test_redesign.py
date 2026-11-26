"""Structural checks for the 2026-11 community-first redesign."""
import base64
import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "kerala.html", "gallery.html"]
MALAYALAM = re.compile(r"[\u0D00-\u0D7F]")


class Tree(HTMLParser):
    """Tracks lang inheritance, template content, headings, landmarks and links."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.ml_without_lang = []
        self.visible_text = []
        self.headings = []
        self.tags = []
        self.nav_links = []
        self._in_nav = False
        self._heading = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if tag == "nav" and a.get("aria-label") == "Main":
            self._in_nav = True
        if self._in_nav and tag == "a":
            self.nav_links.append(a.get("href"))
        if re.fullmatch(r"h[1-6]", tag):
            self._heading = [int(tag[1]), ""]
        if tag not in self.VOID:
            self.stack.append((tag, a.get("lang")))

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_nav = False
        if self._heading and re.fullmatch(r"h[1-6]", tag):
            self.headings.append((self._heading[0], self._heading[1].strip()))
            self._heading = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        in_template = any(t == "template" for t, _ in self.stack)
        in_script = any(t in ("script", "style") for t, _ in self.stack)
        if self._heading is not None:
            self._heading[1] += data
        if in_script:
            return
        if not in_template:
            self.visible_text.append(data)
        if MALAYALAM.search(data):
            langs = [l for _, l in self.stack if l]
            if not langs or langs[-1] != "ml":
                self.ml_without_lang.append(data.strip())


def parse(name):
    t = Tree()
    t.feed((ROOT / name).read_text(encoding="utf-8"))
    return t


class RedesignTests(unittest.TestCase):
    def test_every_malayalam_string_is_marked_lang_ml(self):
        for name in PAGES + ["404.html", "privacy.html", "media-credits.html"]:
            with self.subTest(page=name):
                self.assertEqual(parse(name).ml_without_lang, [])

    def test_existing_malayalam_lines_are_kept_verbatim(self):
        lines = ["ഷെപ്പാർട്ടൺ മലയാളി അസോസിയേഷൻ", "കേരളവും ഷെപ്പാർട്ടണും തമ്മിൽ", "ഞങ്ങളുടെ കമ്മിറ്റി",
                 "കേരളത്തിന്റെ പൈതൃകം", "ഷെമയുടെ ഇവന്റ് ഹൈലൈറ്റുകൾ", "ഓർമ്മയിൽ സൂക്ഷിക്കേണ്ട നിമിഷങ്ങൾ",
                 "ഞങ്ങൾ ആഘോഷിക്കുന്ന പാരമ്പര്യങ്ങൾ", "കേരളത്തിലെ പ്രധാന കാഴ്ചകൾ", "ഷെമ കമ്മ്യൂണിറ്റിയിൽ ചേരൂ"]
        site = "".join((ROOT / p).read_text(encoding="utf-8") for p in PAGES)
        for line in lines:
            self.assertIn(f'lang="ml">{line}<', site)

    def test_titles_have_no_emoji_and_html_is_en_au(self):
        for name in PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            title = re.search(r"<title>(.*?)</title>", html).group(1)
            self.assertFalse(re.search(r"[\U0001F000-\U0001FFFF\u2600-\u27BF]", title), title)
            self.assertIn('<html lang="en-AU">', html)
        self.assertIn("<title>SHEMA – Shepparton Malayalee Association</title>",
                      (ROOT / "index.html").read_text(encoding="utf-8"))

    def test_one_h1_and_ordered_headings_and_landmarks(self):
        for name in PAGES:
            with self.subTest(page=name):
                t = parse(name)
                levels = [lvl for lvl, _ in t.headings]
                self.assertEqual(levels.count(1), 1)
                for a, b in zip(levels, levels[1:]):
                    self.assertLessEqual(b - a, 1, (name, t.headings))
                tags = {tag for tag, _ in t.tags}
                self.assertTrue({"header", "nav", "main", "footer"} <= tags)
                self.assertIn(("a", {"class": "skip-link", "href": "#main"}), t.tags)

    def test_main_nav_is_five_links_with_join_outside_the_menu(self):
        for name in PAGES:
            t = parse(name)
            self.assertEqual(len(t.nav_links), 5, name)
            html = (ROOT / name).read_text(encoding="utf-8")
            nav_end = html.index("</nav>")
            join = html.index('class="btn btn--join header-join"')
            self.assertGreater(join, nav_end, "Join must sit outside the collapsible menu")

    def test_committee_placeholders_are_inert_templates(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        visible = "".join(parse("index.html").visible_text)
        self.assertNotIn("TODO", visible)
        self.assertIn('<template id="tpl-why-join">', html)
        self.assertIn('<template id="tpl-sponsors">', html)
        for name in ("Jacob", "Shinto", "Vice President"):
            self.assertNotIn(name, html)

    def test_old_home_hashes_are_forwarded(self):
        script = (ROOT / "script.js").read_text(encoding="utf-8")
        for old, new in {"video": "/kerala.html#journey", "kerala": "/kerala.html#heritage",
                         "culture": "/kerala.html#traditions", "landmarks": "/kerala.html#landmarks",
                         "products": "/kerala.html#crafts", "community": "#about", "highlights": "#photos",
                         "'leadership-history'": "#committee"}.items():
            self.assertRegex(script, re.escape(old) + r"\s*:\s*'" + re.escape(new) + "'")
        kerala_ids = {a.get("id") for _, a in parse("kerala.html").tags}
        index_ids = {a.get("id") for _, a in parse("index.html").tags}
        self.assertTrue({"journey", "heritage", "traditions", "landmarks", "crafts", "lamp"} <= kerala_ids)
        self.assertTrue({"about", "photos", "committee", "events", "contact", "join", "past-events"} <= index_ids)

    def test_sitemap_canonicals_and_social_meta(self):
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        canonicals = set()
        for name, url in (("index.html", "https://shema.com.au/"), ("kerala.html", "https://shema.com.au/kerala.html"),
                          ("gallery.html", "https://shema.com.au/gallery.html")):
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f'<link rel="canonical" href="{url}" />', html)
            self.assertIn(f"<loc>{url}</loc>", sitemap)
            self.assertIn('property="og:image" content="https://shema.com.au/assets/og/shema-og.jpg"', html)
            canonicals.add(url)
        self.assertEqual(len(canonicals), 3)
        with Image.open(ROOT / "assets/og/shema-og.jpg") as og:
            self.assertEqual(og.size, (1200, 630))
        ld = re.search(r'<script type="application/ld\+json">(.*?)</script>',
                       (ROOT / "index.html").read_text(encoding="utf-8"), re.S).group(1)
        self.assertEqual(json.loads(ld)["@type"], "Organization")

    def test_fonts_are_self_hosted_and_csp_is_tight(self):
        headers = (ROOT / "_headers").read_text(encoding="utf-8")
        self.assertIn("font-src 'self'", headers)
        self.assertNotIn("googleapis", headers)
        self.assertNotIn("wasm-unsafe-eval", headers)
        for page in ROOT.glob("*.html"):
            self.assertNotIn("fonts.googleapis.com", page.read_text(encoding="utf-8"), page.name)
        for font in ("fraunces-latin", "fraunces-italic-latin", "hanken-grotesk-latin",
                     "noto-serif-malayalam-600", "noto-sans-malayalam-500"):
            self.assertTrue((ROOT / f"assets/fonts/{font}.woff2").is_file())
        total = sum(p.stat().st_size for p in (ROOT / "assets/fonts").glob("*.woff2"))
        self.assertLessEqual(total, 220 * 1024)

    def test_3d_assets_are_small_pinned_and_lazy(self):
        glb = ROOT / "assets/3d/lamp.glb"
        self.assertLess(glb.stat().st_size, 300 * 1024)
        self.assertEqual(glb.read_bytes()[:4], b"glTF")
        lamp = (ROOT / "js/lamp.js").read_text(encoding="utf-8")
        mv = ROOT / "vendor/model-viewer-4.4.0/model-viewer.min.js"
        sri = "sha384-" + base64.b64encode(hashlib.sha384(mv.read_bytes()).digest()).decode()
        self.assertIn(sri, lamp)
        self.assertTrue((ROOT / "vendor/model-viewer-4.4.0/LICENSE").is_file())
        for name in PAGES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("model-viewer.min.js", html, "the viewer must only be injected on demand")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-activate="click"', index)
        self.assertIn('data-activate="visible"', (ROOT / "kerala.html").read_text(encoding="utf-8"))
        self.assertIn("prefers-reduced-motion", lamp)

    def test_pipeline_images_have_no_metadata_and_true_sizes(self):
        manifest = json.loads((ROOT / "images/site/manifest.json").read_text(encoding="utf-8"))
        for name, entry in manifest.items():
            for f in entry["files"]:
                with self.subTest(file=f["path"]):
                    with Image.open(ROOT / f["path"]) as im:
                        self.assertEqual(im.size, (f["width"], f["height"]))
                        self.assertFalse(im.getexif())
                        self.assertFalse({"exif", "icc_profile", "xmp"} & im.info.keys())

    def test_every_image_has_alt_and_dimensions(self):
        for name in PAGES:
            for tag, a in parse(name).tags:
                if tag == "img":
                    with self.subTest(page=name, src=a.get("src")):
                        self.assertIn("alt", a)
                        self.assertTrue(a.get("width") and a.get("height"))


if __name__ == "__main__":
    unittest.main()
