"""Render the social share image from tools/og/og.html with the real web fonts.

Needs the local preview server running: python tools/serve.py 8765
Then: python tools/og/render_og.py
"""
import io
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    # tools/* is blocked on Netlify by _redirects; the local server serves it.
    page.goto("http://127.0.0.1:8765/tools/og/og.html", wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    png = page.screenshot(type="png")
    browser.close()

img = Image.open(io.BytesIO(png)).convert("RGB")
out = ROOT / "assets" / "og" / "shema-og.jpg"
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, "JPEG", quality=82, optimize=True, progressive=True)
print(out, img.size, out.stat().st_size)
