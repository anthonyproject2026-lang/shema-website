"""Download self-hosted woff2 fonts (OFL) from Google Fonts, latin + malayalam subsets only.

Run once from the repo root: python tools/fetch_fonts.py
Writes the Google-subset woff2 files, then they were reduced further with fontTools
(uvx --from fonttools[woff] fonttools ...):
  Noto Serif Malayalam: varLib.instancer wght=600, then subset U+0D00-0D7F,U+200C-200D,U+25CC
  Noto Sans Malayalam:  varLib.instancer wght=500, same subset, --layout-features='*' (keeps conjuncts)
  Fraunces:             varLib.instancer opsz=72 wght=500:700 (italic: opsz=72), Latin subset
  Hanken Grotesk:       Latin subset, variable 400-600 kept
Final files: assets/fonts/*.woff2 (about 126 KB in total). @font-face rules live in styles.css.
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
URL = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..700;1,9..144,400"
       "&family=Hanken+Grotesk:wght@400..600&family=Noto+Sans+Malayalam:wght@400..600"
       "&family=Noto+Serif+Malayalam:wght@500..700&display=swap")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req).read().decode("utf-8")
    out = ROOT / "assets" / "fonts"
    out.mkdir(exist_ok=True)
    rules = []
    for subset, body in re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
        fam = re.search(r"font-family: '([^']+)'", body).group(1)
        if not ((subset == "latin" and "Malayalam" not in fam) or subset == "malayalam"):
            continue
        style = re.search(r"font-style: (\w+)", body).group(1)
        weight = re.search(r"font-weight: ([\d ]+);", body).group(1)
        url = re.search(r"url\((.*?)\)", body).group(1)
        urange = re.search(r"unicode-range: (.*?);", body).group(1)
        name = f"{fam.lower().replace(' ', '-')}-{style}-{subset}.woff2"
        urllib.request.urlretrieve(url, out / name)
        size = (out / name).stat().st_size
        print(f"/* {name}: {size} bytes */")
        rules.append(
            f"@font-face {{ font-family: '{fam}'; font-style: {style}; font-weight: {weight}; "
            f"font-display: swap; src: url('/assets/fonts/{name}') format('woff2'); unicode-range: {urange}; }}")
    print("\n".join(rules))


if __name__ == "__main__":
    main()
