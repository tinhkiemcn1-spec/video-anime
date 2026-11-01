"""Study a new reference video: cut rhythm, loudness, contact sheets.

    python -X utf8 analyze_ref.py <video> <out_dir> [--step 20]

Writes <out_dir>/stats.json and sheet_N.jpg (30 frames per sheet with timestamps). Read the sheets
with your eyes: this is how references/phan-tich-video.md was produced."""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("out")
ap.add_argument("--step", type=int, default=20)
a = ap.parse_args()
out = Path(a.out)
(out / "t").mkdir(parents=True, exist_ok=True)
fc = (f"[0:v]fps=8,scale=320:180,split[a][b];[a]select='gt(scene,0.3)',metadata=print:file='scene.txt'[s];"
      f"[b]fps=1/{a.step},scale=640:360[t]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(Path(a.video).resolve()), "-filter_complex", fc, "-map", "[s]", "-f", "null", "-",
                "-map", "[t]", "-q:v", "4", "t/%05d.jpg"], cwd=out, check=True)
times = [float(x) for x in re.findall(r"pts_time:([\d.]+)", (out / "scene.txt").read_text(errors="replace"))]
cuts = []
for t in times:
    if not cuts or t - cuts[-1] > .3:
        cuts.append(t)
gaps = [q - p for p, q in zip(cuts, cuts[1:])] or [0]
p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(Path(a.video).resolve()), "-map", "0:a:0", "-af", "ebur128", "-f", "null", "-"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
stats = {"cuts": len(cuts), "median_s": round(statistics.median(gaps), 2), "mean_s": round(statistics.mean(gaps), 2),
         "lufs": float(lufs[-1]) if lufs else None}
(out / "stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
print(stats)
fs = sorted((out / "t").glob("*.jpg"))
f = ImageFont.load_default(20)
for s in range(0, len(fs), 30):
    part = fs[s:s + 30]
    sh = Image.new("RGB", (6 * 384, ((len(part) + 5) // 6) * 216))
    d = ImageDraw.Draw(sh)
    for i, q in enumerate(part):
        x, y = (i % 6) * 384, (i // 6) * 216
        sh.paste(Image.open(q).resize((384, 216)), (x, y))
        sec = (s + i) * a.step
        d.rectangle((x, y, x + 74, y + 26), fill="black")
        d.text((x + 3, y + 2), f"{sec // 60}:{sec % 60:02d}", fill="yellow", font=f)
    sh.save(out / f"sheet_{s // 30 + 1}.jpg", quality=84)
print("sheets:", out)
