"""Search Wikimedia Commons for real, reusable images and keep their credits.

    python -X utf8 fetch_photos.py <edit> "Genghis Khan portrait" --name thanh_cat [--n 6]

Saves <edit>/photos/<name>_N.jpg, a contact sheet <edit>/photos/<name>_sheet.jpg to look at,
and appends author + licence to <edit>/photos/credits.csv (put these in the video description).
Files are re-encoded through PIL, so only pixel data reaches the project."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "video-anime-skill/1.0 (image lookup for a video editing tool)"}
OK_LICENSE = re.compile(r"public domain|pd|cc0|cc[- ]by", re.I)


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()


ap = argparse.ArgumentParser()
ap.add_argument("edit")
ap.add_argument("query")
ap.add_argument("--name", required=True)
ap.add_argument("--n", type=int, default=6)
a = ap.parse_args()
out = Path(a.edit) / "photos"
out.mkdir(parents=True, exist_ok=True)
q = urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": a.query + " filetype:bitmap", "gsrnamespace": 6,
                            "gsrlimit": a.n * 4, "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1600})
pages = json.loads(get(f"{API}?{q}")).get("query", {}).get("pages", {})
saved = []
for pg in sorted(pages.values(), key=lambda p: p.get("index", 99)):
    ii = pg["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    lic = meta.get("LicenseShortName", {}).get("value", "")
    if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 700 or not OK_LICENSE.search(lic):
        continue
    try:
        im = Image.open(io.BytesIO(get(ii.get("thumburl") or ii["url"]))).convert("RGB")
    except Exception as e:
        print("skip", pg["title"], e)
        continue
    i = len(saved) + 1
    p = out / f"{a.name}_{i}.jpg"
    im.save(p, quality=92)
    author = re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
    saved.append((p, im))
    with open(out / "credits.csv", "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow([p.name, pg["title"], author, lic, ii.get("descriptionurl", "")])
    print(p.name, "|", lic, "|", pg["title"])
    if len(saved) >= a.n:
        break
if saved:
    sh = Image.new("RGB", (1200, 280 * ((len(saved) + 2) // 3)), "white")
    d = ImageDraw.Draw(sh)
    for i, (p, im) in enumerate(saved):
        t = im.copy()
        t.thumbnail((396, 270))
        sh.paste(t, ((i % 3) * 400, (i // 3) * 280))
        d.text(((i % 3) * 400 + 4, (i // 3) * 280 + 4), p.stem, fill="red", font=ImageFont.load_default(20))
    sh.save(out / f"{a.name}_sheet.jpg", quality=85)
print(f"{len(saved)} ảnh -> {out}")
