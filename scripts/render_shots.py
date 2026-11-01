"""Render <edit>/plan.json into Resolve-ready layers + a flat preview.

    python -X utf8 render_shots.py <edit> [--only 3,4,9] [--no-preview]

For every shot:
  layers/sNNN_base.png or .mp4   V1  background, photos, TV, map (mp4 when the camera moves)
  layers/sNNN_act.mov            V2  characters with lip-sync, ProRes 4444 alpha, 30 fps
  layers/sNNN_txt.png            V3  titles, labels, bubbles, marks
Writes <edit>/manifest.json (read by resolve_build.py) and <edit>/preview.mp4.
Character animation is on threes (10 fps), the rhythm of the samples.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import va_bg
import va_cast
import va_host
import va_props
from va_draw import fit_contain, fit_cover, text_outlined

FPS = 30
ANIM = 10
W, H = 1920, 1080
RED_TITLE = (200, 24, 30, 255)
HOST_ANCHOR_X = 480 / 1000


def ease(t):
    return 1 - (1 - t) ** 3


def load_env(wav_path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav_path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32)
    hop = 16000 // ANIM
    n = len(y) // hop
    e = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    return e / (np.percentile(e, 95) + 1e-6)


def mouth_at(env, i, base):
    if i >= len(env):
        return base
    v = env[i]
    if v < .14:
        return base if base != "open" else "closed"
    # alternate shapes so held vowels still read as speech
    return "open" if v > .55 and i % 2 == 0 else ("small" if v > .14 and i % 3 else "wide" if v > .7 else "small")


def host_sprite(sp, mouth, frame, preset):
    eyes = sp.get("eyes", "line")
    if eyes in ("line", "wide") and frame % 37 == 36:
        eyes = "shut"
    sway = round(math.sin(frame * .42 + sp.get("x", 0) * .01))
    return va_host.draw(sp.get("pose", "idle"), eyes, sp.get("brow", "none"), mouth, sway, bool(sp.get("close")), preset)


def place_host(frame_im, sp, spr):
    s = sp.get("scale", 1.0) * (1 if sp.get("close") else .86)
    if s != 1.0:
        spr = spr.resize((round(spr.width * s), round(spr.height * s)), Image.BILINEAR)
    if sp.get("flip"):
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
    ax = spr.width * (1 - HOST_ANCHOR_X if sp.get("flip") else HOST_ANCHOR_X)
    x = sp.get("x", 960) - ax
    y = sp.get("y", H + 50 if not sp.get("close") else None)
    top = (y - spr.height) if y is not None else 40 - 110 * 1.7 * sp.get("scale", 1.0) + 10
    return paste_clip(frame_im, spr, int(x), int(top))


def paste_clip(dst, src, x, y):
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + src.width, dst.width), min(y + src.height, dst.height)
    if x1 > x0 and y1 > y0:
        dst.alpha_composite(src.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))
    return dst


def cast_sprite(a, spec, mouth, frame):
    spr = va_cast.draw(spec, a.get("pose", "idle"), a.get("expr", "normal"), mouth)
    s = a.get("scale", 1.0)
    if s != 1.0:
        spr = spr.resize((round(spr.width * s), round(spr.height * s)), Image.BILINEAR)
    return spr.transpose(Image.FLIP_LEFT_RIGHT) if a.get("flip") else spr


def place_cast(im, a, spr, frame, dur_f):
    s = a.get("scale", 1.0)
    x, y = a.get("x", 960), a.get("y", 1040)
    if a.get("move"):
        x0, x1 = a["move"]
        k = frame / max(dur_f - 1, 1)
        if a.get("loop"):
            k = (k * a["loop"]) % 1
        x = x0 + (x1 - x0) * k
        y -= abs(math.sin(frame * 1.4)) * 16 * s  # the little hop of the walk cycles
    y += (frame // 5 % 2) * 2  # breathing
    return paste_clip(im, spr, int(x - spr.width / 2), int(y - va_cast.FEET * s))


def crowd_layer(a, spec):
    """Copy-paste rows of the same soldier, back rows first (see sample at war 0:36)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = a.get("scale", .4)
    spr = cast_sprite({**a, "scale": s}, spec, "closed", 0)
    cols, rows = a["crowd"]
    x0, y0 = a.get("x", 1200), a.get("y", 1040)
    dx, dy = a.get("dx", 130 * s / .4), a.get("dy", 110 * s / .4)
    for r in range(rows - 1, -1, -1):
        for k in range(cols):
            paste_clip(im, spr, int(x0 + k * dx - spr.width / 2 + (r % 2) * dx * .3), int(y0 - r * dy - va_cast.FEET * s))
    return im


def text_layer(shot, plan):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bg = shot.get("bg", "white")
    if shot.get("title"):
        red = bg == "parchment"
        im.alpha_composite(text_outlined((W, H), shot["title"], (960, shot.get("title_y", 90)), shot.get("title_size", 74 if red else 72),
                                         fill=RED_TITLE if red else (20, 18, 20, 255), outline=(255, 240, 210, 255) if red else None,
                                         ow=5, kind="bold" if red else "hand"))
    if shot.get("sub"):
        im.alpha_composite(text_outlined((W, H), shot["sub"], (shot.get("sub_x", 300), shot.get("sub_y", 420)), 46))
    for l in shot.get("labels", []):
        plate = l.get("style", "sticker") == "sticker"
        im.alpha_composite(text_outlined((W, H), l["text"], (l["x"], l["y"]), l.get("size", 58),
                                         fill=(255, 255, 255, 255) if plate else (20, 18, 20, 255),
                                         outline=(14, 12, 14, 255) if plate else None, ow=9, kind="hand"))
    b = shot.get("bubble")
    if b:
        img = None
        if b.get("image"):
            img = Image.open(resolve(plan, b["image"]))
        elif b.get("char"):
            img = va_cast.draw(plan["cast"][b["char"]], b.get("pose", "idle"), b.get("expr", "normal"))
        im.alpha_composite(va_props.bubble(b.get("text"), img, b.get("x", 960), b.get("y", 300), b.get("w", 440), b.get("h", 300),
                                           b.get("kind", "speech"), tuple(b.get("tail", (-1, 1)))))
    for m in shot.get("marks", []):
        im.alpha_composite(va_props.mark(m["kind"], m["x"], m["y"], m.get("s", 1.0)))
    return im


def resolve(plan, p):
    p = Path(p)
    return p if p.is_absolute() else plan["_edit"] / p


class Pipe:
    def __init__(self, path, rate, alpha, size=(W, H)):
        if alpha:
            codec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-qscale:v", "11", "-vendor", "apl0",
                     "-alpha_bits", "8", "-color_range", "tv"]
        else:
            codec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p"]
        self.p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba" if alpha else "rgb24", "-s", f"{size[0]}x{size[1]}",
                                   "-r", str(rate), "-i", "-", "-r", str(FPS), *codec, str(path)], stdin=subprocess.PIPE)

    def write(self, im):
        self.p.stdin.write(im.tobytes())

    def close(self):
        self.p.stdin.close()
        if self.p.wait():
            sys.exit("ffmpeg failed")


def strip_frames(shot, plan):
    """Camera moves over a long sheet with heavy motion blur: the title stack (vertical whip)
    and the list recap. Yields (frame index, RGB image) at 30 fps."""
    items = shot["items"]
    dur = round((shot["end"] - shot["t"]) * FPS)
    vertical = shot["type"] == "stack"
    bgim = va_bg.get(shot.get("bg", "parchment" if vertical else "white"))
    if vertical:
        sheet = Image.new("RGBA", (W, H * len(items)), (0, 0, 0, 0))
        for i, it in enumerate(items):
            if it.get("title"):
                sheet.alpha_composite(text_outlined((W, H), it["title"], (960, 90), 74, fill=RED_TITLE, outline=(255, 240, 210, 255), ow=5, kind="bold"), (0, i * H))
            if it.get("char"):
                spr = va_cast.draw(plan["cast"][it["char"]], it.get("pose", "idle"), it.get("expr", "normal")).resize((608, 720))
                sheet.alpha_composite(spr, (656, i * H + 240))
            if it.get("image"):
                p = fit_contain(Image.open(resolve(plan, it["image"])).convert("RGBA"), 900, 760)
                sheet.alpha_composite(p, (960 - p.width // 2, i * H + 220))
        stops = [(0, i * H) for i in range(len(items))]
    else:
        cols = shot.get("cols", 3)
        rows = (len(items) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * 760 + 400, rows * 720 + 200), (0, 0, 0, 0))
        palette = [(84, 236, 206, 255), (252, 232, 96, 255), (250, 150, 230, 255), (160, 240, 150, 255), (110, 190, 245, 255), (250, 160, 120, 255)]
        stops = []
        for i, it in enumerate(items):
            img = Image.open(resolve(plan, it["image"])) if it.get("image") else None
            if it.get("char"):
                img = va_cast.draw(plan["cast"][it["char"]], "idle", it.get("expr", "normal"))
            x, y = 200 + (i % cols) * 760 + ((i // cols) % 2) * 240, 100 + (i // cols) * 720
            sheet.alpha_composite(va_props.badge(img, it["text"], bg=palette[i % len(palette)]), (x, y))
            stops.append((max(0, x + 260 - 1100), max(0, y + 300 - 540)))
    hold = dur / len(stops)
    tr = min(10, int(hold * .4))
    a = np.asarray(sheet, np.float32)
    bg = np.asarray(bgim.convert("RGB"), np.float32)

    def at(x, y):
        x, y = int(x), int(y)
        crop = np.zeros((H, W, 4), np.float32)
        h = min(H, a.shape[0] - y)
        w = min(W, a.shape[1] - x)
        if h > 0 and w > 0:
            crop[:h, :w] = a[y:y + h, x:x + w]
        al = crop[..., 3:] / 255
        return crop[..., :3] * al + bg * (1 - al)
    still = [Image.fromarray(at(*p).astype(np.uint8)) for p in stops]
    for f in range(dur):
        k = int(f // hold)
        ph = f - k * hold
        if k + 1 < len(stops) and ph >= hold - tr:
            t = (ph - (hold - tr)) / tr
            p0, p1 = stops[k], stops[k + 1]
            subs = [at(p0[0] + (p1[0] - p0[0]) * ease(t + j / (tr * 6)), p0[1] + (p1[1] - p0[1]) * ease(t + j / (tr * 6))) for j in range(6)]
            yield f, Image.fromarray(np.mean(subs, axis=0).astype(np.uint8))
        else:
            yield f, still[k]


def render_base(shot, plan, prev_flat):
    t = shot["type"]
    if t in ("host", "card"):
        im = va_bg.get(shot.get("bg", "white"), shot.get("seed", 1), shot.get("mood", "day")).copy()
    elif t == "scene":
        im = va_bg.get(shot.get("bg", "field"), shot.get("seed", 1), shot.get("mood", "day")).copy()
    elif t == "photo":
        im = va_bg.get(shot.get("bg", "white")).copy()
        p = fit_contain(Image.open(resolve(plan, shot["photo"])).convert("RGBA"), 1160, 960)
        im.alpha_composite(p, (60 + (1160 - p.width) // 2, (1080 - p.height) // 2))
    elif t == "map":
        im = fit_cover(Image.open(resolve(plan, shot["photo"])).convert("RGBA"), W, H)
        for r in shot.get("rings", []):
            im.alpha_composite(va_props.ring(r["x"], r["y"], r.get("r", 70)))
    elif t == "tv":
        im = va_bg.get(shot.get("bg", "white")).copy()
        im.alpha_composite(va_props.tv_desk(prev_flat))
    else:
        sys.exit(f"unknown shot type {t}")
    for a in shot.get("cast", []):
        if a.get("crowd"):
            im.alpha_composite(crowd_layer(a, plan["cast"][a["id"]]))
    return im


def actors_of(shot):
    out = []
    t = shot["type"]
    if shot.get("host") or t in ("host", "photo", "map", "tv"):
        d = dict(shot.get("host") or {})
        if t == "host":
            d.setdefault("x", 960)
            d.setdefault("pose", shot.get("pose", "idle"))
        elif t == "photo":
            d.setdefault("x", 1560)
            d.setdefault("pose", "present")
            d.setdefault("scale", .92)
        elif t == "map":
            d.setdefault("x", 1560)
            d.setdefault("pose", "point")
        elif t == "tv":
            d.setdefault("x", 1400)
            d.setdefault("close", True)
            d.setdefault("pose", "hip")
            d.setdefault("eyes", "wide")
            d.setdefault("mouth", "smirk")
        d.setdefault("talk", True)
        out.append(("host", d))
    for a in shot.get("cast", []):
        if not a.get("crowd"):
            out.append(("cast", a))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args()
    edit = Path(args.edit).resolve()
    plan = json.loads((edit / "plan.json").read_text(encoding="utf-8"))
    plan["_edit"] = edit
    preset = plan.get("host_preset", "mau")
    env = load_env(resolve(plan, plan["vo"]))
    lay = edit / "layers"
    lay.mkdir(exist_ok=True)
    only = {int(x) for x in args.only.split(",") if x}
    prev = None
    man = json.loads((edit / "manifest.json").read_text(encoding="utf-8")) if (edit / "manifest.json").exists() and only else {"clips": []}
    if only:
        man["clips"] = [c for c in man["clips"] if c["shot"] not in only]
    pv = None if args.no_preview or only else Pipe(edit / "_preview_video.mp4", FPS, False, (960, 540))
    for i, shot in enumerate(plan["shots"]):
        n = f"s{i:03d}"
        dur_f = round(shot["end"] * FPS) - round(shot["t"] * FPS)
        if only and i not in only:
            continue
        # ---- base
        moving = shot["type"] in ("stack", "list")
        if moving:
            base_path = lay / f"{n}_base.mp4"
            bp = Pipe(base_path, FPS, False)
            flat = None
            fr = []
            for f, im in strip_frames(shot, plan):
                bp.write(im)
                if pv and f % 3 == 0:
                    fr.append(im)
                flat = im
            bp.close()
            base = None
        else:
            base = render_base(shot, plan, prev)
            base_path = lay / f"{n}_base.png"
            base.convert("RGB").save(base_path)
            flat = base
        man["clips"].append({"shot": i, "track": 1, "file": str(base_path), "t": shot["t"], "end": shot["end"], "kind": "video" if moving else "still"})
        txt = text_layer(shot, plan)
        has_txt = txt.getbbox() is not None
        if has_txt:
            txt_path = lay / f"{n}_txt.png"
            txt.save(txt_path)
            man["clips"].append({"shot": i, "track": 3, "file": str(txt_path), "t": shot["t"], "end": shot["end"], "kind": "still"})
        # ---- actors
        acts = actors_of(shot)
        n_anim = max(1, round(dur_f / FPS * ANIM))
        f0 = int(shot["t"] * ANIM)
        if acts:
            act_path = lay / f"{n}_act.mov"
            ap_ = Pipe(act_path, ANIM, True)
            for k in range(n_anim):
                fr_im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                for kind, a in acts:
                    base_mouth = a.get("mouth", "closed")
                    mouth = mouth_at(env, f0 + k, base_mouth) if a.get("talk") else base_mouth
                    if kind == "host":
                        place_host(fr_im, a, host_sprite(a, mouth, f0 + k, preset))
                    else:
                        spec = plan["cast"][a["id"]]
                        place_cast(fr_im, a, cast_sprite(a, spec, mouth, f0 + k), k, n_anim)
                ap_.write(fr_im)
                if pv and not moving:
                    c = flat.copy()
                    c.alpha_composite(fr_im)
                    if has_txt:
                        c.alpha_composite(txt)
                    pv.write(c.convert("RGB").resize((960, 540), Image.BILINEAR))
                    for _ in range(2):
                        pv.write(c.convert("RGB").resize((960, 540), Image.BILINEAR))
                if k == 0:
                    snap = flat.copy().convert("RGBA")
                    snap.alpha_composite(fr_im)
                    if has_txt:
                        snap.alpha_composite(txt)
                    if shot["type"] == "scene":
                        prev = snap
            ap_.close()
            man["clips"].append({"shot": i, "track": 2, "file": str(act_path), "t": shot["t"], "end": shot["end"], "kind": "video"})
        elif pv and not moving:
            c = flat.copy().convert("RGBA")
            if has_txt:
                c.alpha_composite(txt)
            c = c.convert("RGB").resize((960, 540), Image.BILINEAR)
            for _ in range(n_anim * 3):
                pv.write(c)
        if pv and moving:
            for im in fr:
                for _ in range(3):
                    pv.write(im.resize((960, 540), Image.BILINEAR))
        if shot.get("meme"):
            m = shot["meme"]
            man["clips"].append({"shot": i, "track": 4, "file": str(resolve(plan, m["file"])), "t": shot["t"], "end": shot["end"],
                                 "kind": "video", "opacity": m.get("opacity", .55), "src": m.get("start", 0)})
        for s in ([shot["sfx"]] if isinstance(shot.get("sfx"), str) else shot.get("sfx", [])):
            nm, at = (s.split("@") + ["0"])[:2]
            man["clips"].append({"shot": i, "track": -2, "file": str(Path(__file__).resolve().parent.parent / "assets" / "sfx" / f"{nm}.wav"),
                                 "t": shot["t"] + float(at), "end": None, "kind": "audio", "gain": plan.get("sfx_db", -8)})
        print(n, shot["type"], f"{shot['end'] - shot['t']:.1f}s", flush=True)
    man.update({"vo": str(resolve(plan, plan["vo"])), "music": str(resolve(plan, plan["music"])) if plan.get("music") else None,
                "music_db": plan.get("music_db", -24), "title": plan.get("title", edit.name), "duration": plan["shots"][-1]["end"], "fps": FPS})
    (edit / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    if pv:
        pv.close()
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(edit / "_preview_video.mp4"), "-i", str(resolve(plan, plan["vo"])), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-shortest", str(edit / "preview.mp4")], check=True)
        (edit / "_preview_video.mp4").unlink()
    print("manifest + preview written:", edit)


if __name__ == "__main__":
    main()
