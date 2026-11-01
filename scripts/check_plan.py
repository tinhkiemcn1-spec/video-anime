"""Validate <edit>/plan.json before rendering. Prints PLAN OK or the list of problems.

    python -X utf8 check_plan.py <edit>
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

import va_bg
import va_cast
import va_host

SFX = {p.stem for p in (Path(__file__).resolve().parent.parent / "assets" / "sfx").glob("*.wav")}
TYPES = {"host", "photo", "card", "scene", "tv", "map", "list", "stack"}
MARKS = {"x", "anger", "sweat", "laugh", "!!!", "???"}

edit = Path(sys.argv[1])
plan = json.loads((edit / "plan.json").read_text(encoding="utf-8"))
err, warn = [], []
shots = plan["shots"]
vo = edit / plan["vo"] if not Path(plan["vo"]).is_absolute() else Path(plan["vo"])
if not vo.exists():
    err.append(f"thiếu VO: {vo}")
else:
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(vo)], capture_output=True, text=True).stdout)
    if abs(shots[-1]["end"] - d) > .5:
        err.append(f"shot cuối kết thúc {shots[-1]['end']:.2f}s, VO dài {d:.2f}s")
if shots[0]["t"] != 0:
    err.append("shot đầu phải bắt đầu ở 0")
for i, s in enumerate(shots):
    tag = f"shot {i}"
    if s.get("type") not in TYPES:
        err.append(f"{tag}: type '{s.get('type')}' không có")
    if i and abs(s["t"] - shots[i - 1]["end"]) > 1e-3:
        err.append(f"{tag}: hở/chồng với shot trước ({shots[i - 1]['end']} -> {s['t']})")
    dur = s["end"] - s["t"]
    if dur < .4:
        err.append(f"{tag}: quá ngắn ({dur:.2f}s)")
    if dur > 25:
        warn.append(f"{tag}: {dur:.1f}s, mẫu hiếm khi giữ một cảnh quá 20s")
    if s.get("bg") and s["bg"] not in va_bg.NAMES:
        err.append(f"{tag}: bg '{s['bg']}' không có ({', '.join(va_bg.NAMES)})")
    for k in ("photo",):
        if s.get(k) and not (edit / s[k]).exists() and not Path(s[k]).exists():
            err.append(f"{tag}: thiếu file {s[k]}")
    if s.get("type") in ("photo", "map") and not s.get("photo"):
        err.append(f"{tag}: type {s['type']} cần 'photo'")
    h = s.get("host") or {}
    if h.get("pose") and h["pose"] not in va_host.POSES:
        err.append(f"{tag}: host pose '{h['pose']}' không có")
    if h.get("eyes") and h["eyes"] not in va_host.EYES:
        err.append(f"{tag}: host eyes '{h['eyes']}' không có")
    if h.get("brow") and h["brow"] not in va_host.BROWS:
        err.append(f"{tag}: host brow '{h['brow']}' không có")
    for a in s.get("cast", []):
        if a.get("id") not in plan.get("cast", {}):
            err.append(f"{tag}: nhân vật '{a.get('id')}' chưa khai báo trong cast")
        if a.get("pose") and a["pose"] not in va_cast.POSES:
            err.append(f"{tag}: pose '{a['pose']}' không có")
        if a.get("expr") and a["expr"] not in va_cast.EXPR:
            err.append(f"{tag}: expr '{a['expr']}' không có")
    for m in s.get("marks", []):
        if m.get("kind") not in MARKS:
            err.append(f"{tag}: mark '{m.get('kind')}' không có")
    for x in ([s["sfx"]] if isinstance(s.get("sfx"), str) else s.get("sfx", [])):
        if x.split("@")[0] not in SFX:
            err.append(f"{tag}: sfx '{x}' không có ({', '.join(sorted(SFX))})")
    if s.get("meme") and not ((edit / s["meme"]["file"]).exists() or Path(s["meme"]["file"]).exists()):
        err.append(f"{tag}: thiếu meme {s['meme']['file']}")
for c, sp in plan.get("cast", {}).items():
    if sp.get("hat", "none") not in va_cast.HATS:
        err.append(f"cast {c}: hat '{sp['hat']}' không có")
    if sp.get("hair", "short") not in va_cast.HAIRS:
        err.append(f"cast {c}: hair '{sp['hair']}' không có")
    if sp.get("beard", "none") not in va_cast.BEARDS:
        err.append(f"cast {c}: beard '{sp['beard']}' không có")
durs = [s["end"] - s["t"] for s in shots]
kinds = Counter(s.get("type") for s in shots)
print(f"{len(shots)} shots, trung vị {statistics.median(durs):.1f}s (mẫu: 5-6s), {len(shots) / (shots[-1]['end'] / 60):.1f} cảnh/phút (mẫu: 7-8)")
print("loại:", dict(kinds))
for w in warn:
    print("CẢNH BÁO", w)
for e in err:
    print("LỖI", e)
if err:
    sys.exit(1)
print("PLAN OK")
