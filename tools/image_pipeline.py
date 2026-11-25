"""SHEMA image pipeline.

Resizes real repo photos to 480 / 960 / 1600 px (never upscaling), exports AVIF + WebP
(+ JPEG fallback), strips all metadata (EXIF incl. GPS, ICC, XMP), and writes
images/site/manifest.json with the exact width/height of every file so the HTML
can carry width/height attributes (no layout shift).

Usage (repo root):  python tools/image_pipeline.py
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "images" / "site"
WIDTHS = (480, 960, 1600)

# name, source, crop aspect (w/h) or None, vertical focus 0..1 for crops, formats
JOBS = [
    ("hero-backwaters", "images/kerala-backwaters.png", 16 / 10, 0.55, ("webp", "avif")),
    ("event-mayor", "images/event-mayor.jpg", 4 / 3, 0.45, ("avif", "webp", "jpg")),
    ("event-lamp", "images/event-lamp.jpg", 4 / 3, 0.5, ("avif", "webp", "jpg")),
    ("event-mayor-wide", "images/event-mayor.jpg", None, 0.5, ("avif", "webp", "jpg")),
    ("event-lamp-wide", "images/event-lamp.jpg", None, 0.5, ("avif", "webp", "jpg")),
    ("committee-antony", "images/committee-antony.jpg", 4 / 5, 0.22, ("avif", "webp", "jpg")),
    ("committee-anu", "images/committee-anu.png", 4 / 5, 0.25, ("avif", "webp", "jpg")),
    ("committee-arun", "images/committee-arun.png", 4 / 5, 0.25, ("avif", "webp", "jpg")),
    ("kerala-intro-poster", "images/0601-cover.jpg", 16 / 9, 0.5, ("avif", "webp", "jpg")),
    # Blender render (tools/blender/build_lamp.py), flattened onto ink-900
    ("lamp-lit", "tools/blender/out/lamp-lit.png", None, 0.5, ("avif", "webp", "jpg")),
]
INK_900 = (42, 29, 20)
COMMITTEE_WIDTHS = (240, 480)  # displayed at max 220 CSS px


def crop_to(img, aspect, focus):
    w, h = img.size
    if aspect is None:
        return img
    if w / h > aspect:  # too wide: crop sides, centred
        nw = round(h * aspect)
        left = (w - nw) // 2
        return img.crop((left, 0, left + nw, h))
    nh = round(w / aspect)
    top = round((h - nh) * focus)
    return img.crop((0, top, w, top + nh))


def clean(img):
    """Return a fresh RGB image with no metadata attached."""
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, INK_900 + (255,))
        bg.alpha_composite(img)
        img = bg
    img = img.convert("RGB")
    fresh = Image.new("RGB", img.size)
    fresh.paste(img)
    return fresh


def save(img, path, fmt):
    kw = {"webp": dict(quality=78, method=6), "avif": dict(quality=55, speed=4),
          "jpg": dict(quality=80, optimize=True, progressive=True)}[fmt]
    img.save(path, "JPEG" if fmt == "jpg" else fmt.upper(), **kw)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, src, aspect, focus, fmts in JOBS:
        with Image.open(ROOT / src) as raw:
            base = crop_to(clean(raw), aspect, focus)
        widths = COMMITTEE_WIDTHS if name.startswith("committee-") else WIDTHS
        sizes = sorted({min(w, base.width) for w in widths})
        entry = {"source": src, "aspect": aspect, "files": []}
        for w in sizes:
            h = round(base.height * w / base.width)
            resized = base.resize((w, h), Image.LANCZOS)
            for fmt in fmts:
                path = OUT / f"{name}-{w}.{fmt}"
                save(resized, path, fmt)
                with Image.open(path) as check:
                    assert not check.getexif(), path
                    assert not ({"exif", "icc_profile", "xmp"} & check.info.keys()), path
                    real = check.size
                entry["files"].append({"path": path.relative_to(ROOT).as_posix(), "format": fmt,
                                       "width": real[0], "height": real[1],
                                       "bytes": path.stat().st_size,
                                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                print(f"{path.relative_to(ROOT).as_posix():48s} {real[0]}x{real[1]} {path.stat().st_size:>8} B")
        manifest[name] = entry
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
