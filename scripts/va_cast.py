"""Chibi cast: big round head, legless pawn body, floating mitten hands.
A character is a plain dict, so a whole story's cast fits in the plan:
  {"skin":"light","hair":"short","hair_col":"#3a2a20","hat":"crown","beard":"full",
   "robe":"#8a2030","sash":"#d8b040","flag":null,"eyes":"normal"}
flag = {"bands":["#e00","#fff","#e00"],"dir":"h"} turns the head into a country ball."""
from __future__ import annotations

import json
from functools import lru_cache

from PIL import Image, ImageDraw

from va_draw import Canvas, INK, mitten

SKIN = {"light": (254, 234, 226, 255), "tan": (232, 196, 160, 255), "brown": (160, 112, 84, 255),
        "dark": (112, 76, 58, 255), "pale": (236, 240, 244, 255), "blue": (150, 200, 230, 255)}
HAIRS = ("none", "short", "side", "long", "bob", "bun", "bald", "spiky", "curly", "princess")
HATS = ("none", "crown", "turban", "helmet", "officer", "conical", "wizard", "tophat", "cap", "headwrap", "royal_cap")
BEARDS = ("none", "mustache", "goatee", "full", "long")
POSES = ("idle", "point", "fist", "pray", "raised", "think", "cross", "sword", "scroll", "hand_chin")
BODY = 300
FEET = 300 + 135 + BODY  # sprite y of the robe hem
EXPR = ("normal", "angry", "sad", "smug", "shock", "happy", "sleep", "cry")


def rgba(h):
    if isinstance(h, (tuple, list)):
        return tuple(h) if len(h) == 4 else (*h, 255)
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def darker(c, k=.72):
    return (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255)


def _hair_back(c, cx, cy, r, kind, col):
    if kind in ("long", "princess"):
        c.shape([(cx - r * 1.08, cy - r * .1), (cx - r * 1.14, cy + r * 1.1), (cx - r * .4, cy + r * 1.3),
                 (cx + r * .4, cy + r * 1.3), (cx + r * 1.14, cy + r * 1.1), (cx + r * 1.08, cy - r * .1)], col, 9)
    elif kind == "bob":
        c.shape([(cx - r * 1.1, cy - r * .2), (cx - r * 1.1, cy + r * .78), (cx - r * .4, cy + r * .9),
                 (cx + r * .4, cy + r * .9), (cx + r * 1.1, cy + r * .78), (cx + r * 1.1, cy - r * .2)], col, 9)
    elif kind == "bun":
        c.ellipse(cx, cy - r * 1.18, r * .42, r * .36, col, 9)


def _hair_front(c, cx, cy, r, kind, col):
    if kind in ("none", "bald"):
        if kind == "bald":
            c.shape([(cx - r * 1.0, cy + r * .1), (cx - r * .98, cy - r * .32), (cx - r * .74, cy - r * .5)], col, 7)
            c.shape([(cx + r * 1.0, cy + r * .1), (cx + r * .98, cy - r * .32), (cx + r * .74, cy - r * .5)], col, 7)
        return
    top = [(cx - r * 1.02, cy - r * .02), (cx - r * .92, cy - r * .74), (cx - r * .3, cy - r * 1.08), (cx + r * .3, cy - r * 1.08),
           (cx + r * .92, cy - r * .74), (cx + r * 1.02, cy - r * .02)]
    if kind == "spiky":
        fringe = [(cx + r * .8, cy - r * .3, 1), (cx + r * .46, cy - r * .56), (cx + r * .24, cy - r * .3, 1),
                  (cx - r * .06, cy - r * .56), (cx - r * .32, cy - r * .3, 1), (cx - r * .6, cy - r * .54), (cx - r * .84, cy - r * .22, 1)]
    elif kind == "side":
        fringe = [(cx + r * .84, cy - r * .16, 1), (cx + r * .3, cy - r * .62), (cx - r * .3, cy - r * .3), (cx - r * .84, cy - r * .1, 1)]
    elif kind == "curly":
        for a in range(-5, 6):
            c.ellipse(cx + a * r * .2, cy - r * (.8 + .22 * (1 - abs(a) / 5)), r * .26, r * .24, col, 7)
        fringe = [(cx + r * .86, cy - r * .3, 1), (cx, cy - r * .5), (cx - r * .86, cy - r * .3, 1)]
    else:
        fringe = [(cx + r * .9, cy - r * .1, 1), (cx + r * .4, cy - r * .48), (cx - r * .4, cy - r * .48), (cx - r * .9, cy - r * .1, 1)]
    c.shape(top + fringe, col, 9)


def _hat(c, cx, cy, r, kind, col):
    k = col or {"crown": rgba("#f0a020"), "turban": rgba("#f0ece0"), "helmet": rgba("#7a7f88"), "officer": rgba("#94a8ae"),
                "conical": rgba("#e0c070"), "wizard": rgba("#6a3a90"), "tophat": rgba("#2c2c30"), "cap": rgba("#3a5a8a"),
                "headwrap": rgba("#2f5040"), "royal_cap": rgba("#7a4a70")}.get(kind)
    if kind == "crown":
        y = cy - r * .72
        c.shape([(cx - r * .86, y + r * .08, 1), (cx - r * .92, y - r * .62, 1), (cx - r * .46, y - r * .22, 1), (cx, y - r * .8, 1),
                 (cx + r * .46, y - r * .22, 1), (cx + r * .92, y - r * .62, 1), (cx + r * .86, y + r * .08, 1)], k, 9, soft=False)
        c.ellipse(cx, y - r * .1, r * .1, r * .1, rgba("#c02030"), 6)
    elif kind == "turban":
        c.shape([(cx - r * 1.06, cy - r * .3), (cx - r * 1.1, cy - r * .9), (cx - r * .4, cy - r * 1.36), (cx + r * .5, cy - r * 1.34),
                 (cx + r * 1.12, cy - r * .8), (cx + r * 1.04, cy - r * .3), (cx, cy - r * .56)], k, 9)
        c.line([(cx - r * .9, cy - r * .9), (cx, cy - r * .66), (cx + r * .9, cy - r * 1.02)], 6)
        c.line([(cx - r * .5, cy - r * 1.24), (cx + r * .3, cy - r * .92), (cx + r * .96, cy - r * .56)], 6)
    elif kind == "helmet":
        c.shape([(cx - r * 1.06, cy - r * .2), (cx - r * .96, cy - r * .84), (cx, cy - r * 1.2), (cx + r * .96, cy - r * .84),
                 (cx + r * 1.06, cy - r * .2), (cx, cy - r * .46)], k, 9)
        c.shape([(cx, cy - r * 1.14), (cx - r * .3, cy - r * 1.64), (cx + r * .5, cy - r * 1.7), (cx + r * .2, cy - r * 1.14)],
                rgba("#c03020"), 8)
    elif kind == "officer":
        c.shape([(cx - r * .96, cy - r * .5, 1), (cx - r * 1.26, cy - r * .96), (cx + r * .3, cy - r * 1.52), (cx + r * 1.26, cy - r * .96),
                 (cx + r * .96, cy - r * .5, 1)], k, 10)
        c.shape([(cx - r * 1.0, cy - r * .5, 1), (cx + r * 1.0, cy - r * .5, 1), (cx + r * .66, cy - r * .3), (cx - r * .66, cy - r * .3)],
                rgba("#4a3a30"), 8)
    elif kind == "conical":
        c.shape([(cx - r * 1.36, cy - r * .42, 1), (cx, cy - r * 1.5, 1), (cx + r * 1.36, cy - r * .42, 1)], k, 9, soft=False)
    elif kind == "wizard":
        c.shape([(cx - r * 1.1, cy - r * .5, 1), (cx - r * .1, cy - r * 2.0, 1), (cx + r * 1.1, cy - r * .5, 1)], k, 9, soft=False)
    elif kind == "tophat":
        c.rect(cx - r * .7, cy - r * 1.7, cx + r * .7, cy - r * .62, k, 9)
        c.rect(cx - r * 1.1, cy - r * .7, cx + r * 1.1, cy - r * .54, k, 9)
    elif kind == "cap":
        c.shape([(cx - r * .96, cy - r * .42), (cx - r * .8, cy - r * 1.04), (cx + r * .8, cy - r * 1.04), (cx + r * .96, cy - r * .42)], k, 9)
    elif kind == "headwrap":
        c.shape([(cx - r * 1.08, cy + r * .9), (cx - r * 1.1, cy - r * .9), (cx, cy - r * 1.18), (cx + r * 1.1, cy - r * .9),
                 (cx + r * 1.08, cy + r * .9), (cx + r * .84, cy + r * .5), (cx + r * .84, cy - r * .28), (cx, cy - r * .5),
                 (cx - r * .84, cy - r * .28), (cx - r * .84, cy + r * .5)], k, 9)
    elif kind == "royal_cap":
        c.shape([(cx - r * .98, cy - r * .42), (cx - r * .84, cy - r * 1.04), (cx, cy - r * 1.22), (cx + r * .84, cy - r * 1.04),
                 (cx + r * .98, cy - r * .42), (cx, cy - r * .6)], k, 9)
        c.line([(cx - r * .34, cy - r * 1.14), (cx - r * .34, cy - r * .56)], 6)
        c.line([(cx + r * .34, cy - r * 1.14), (cx + r * .34, cy - r * .56)], 6)


def _face(c, cx, cy, r, expr, mouth, skin):
    ey, ex = cy + r * .08, r * .4
    lw = 7
    if expr in ("sleep",):
        for s in (-1, 1):
            c.line([(cx + s * ex - 16, ey), (cx + s * ex, ey + 8), (cx + s * ex + 16, ey)], lw)
    elif expr == "happy":
        for s in (-1, 1):
            c.line([(cx + s * ex - 16, ey + 6), (cx + s * ex, ey - 8), (cx + s * ex + 16, ey + 6)], lw)
    elif expr == "smug":
        for s in (-1, 1):
            c.line([(cx + s * ex - 22, ey), (cx + s * ex + 22, ey)], lw)
            c.ellipse(cx + s * ex + 2, ey + 8, 6, 6, INK, 0)
    elif expr == "shock":
        for s in (-1, 1):
            c.ellipse(cx + s * ex, ey, 17, 21, (255, 255, 255, 255), 6)
            c.ellipse(cx + s * ex, ey, 4, 4, INK, 0)
    else:
        for s in (-1, 1):
            c.ellipse(cx + s * ex, ey, 15, 11, (255, 255, 255, 255), 6)
            c.ellipse(cx + s * ex, ey, 6, 6, INK, 0)
    if expr == "angry":
        c.line([(cx - ex - 26, ey - 34), (cx - ex + 22, ey - 14)], lw + 1)
        c.line([(cx + ex + 26, ey - 34), (cx + ex - 22, ey - 14)], lw + 1)
    elif expr in ("sad", "cry"):
        c.line([(cx - ex - 24, ey - 16), (cx - ex + 22, ey - 32)], lw)
        c.line([(cx + ex + 24, ey - 16), (cx + ex - 22, ey - 32)], lw)
    elif expr not in ("sleep", "happy"):
        for s in (-1, 1):
            c.line([(cx + s * ex - 22, ey - 26), (cx + s * ex, ey - 34), (cx + s * ex + 22, ey - 26)], 6)
    if expr == "cry":
        c.shape([(cx + ex + 6, ey + 18), (cx + ex - 8, ey + 44), (cx + ex + 6, ey + 58), (cx + ex + 20, ey + 44)], (120, 190, 240, 255), 5)
    my = cy + r * .56
    if mouth == "small":
        c.ellipse(cx, my, 10, 9, (160, 8, 24, 255), 6)
    elif mouth == "open":
        c.ellipse(cx, my, 14, 18, (160, 8, 24, 255), 6)
    elif mouth == "wide":
        c.shape([(cx - 22, my - 8, 1), (cx + 22, my - 8, 1), (cx, my + 18)], (160, 8, 24, 255), 6)
    elif mouth == "frown" or expr in ("sad", "cry", "angry"):
        c.line([(cx - 14, my + 5), (cx, my - 2), (cx + 14, my + 5)], 6)
    elif expr in ("smug", "happy"):
        c.line([(cx - 16, my - 3), (cx, my + 6), (cx + 18, my - 5)], 6)
    else:
        c.line([(cx - 11, my), (cx + 11, my)], 6)


def _beard(c, cx, cy, r, kind, col):
    if kind == "mustache":
        c.shape([(cx, cy + r * .42), (cx - r * .36, cy + r * .46), (cx - r * .4, cy + r * .56), (cx, cy + r * .5),
                 (cx + r * .4, cy + r * .56), (cx + r * .36, cy + r * .46)], col, 5)
    elif kind == "goatee":
        c.shape([(cx - r * .2, cy + r * .68), (cx, cy + r * 1.12), (cx + r * .2, cy + r * .68)], col, 6)
    elif kind in ("full", "long"):
        d = 1.26 if kind == "full" else 1.7
        c.shape([(cx - r * .98, cy + r * .2), (cx - r * .68, cy + r * d * .86), (cx, cy + r * d), (cx + r * .68, cy + r * d * .86),
                 (cx + r * .98, cy + r * .2), (cx + r * .6, cy + r * .42), (cx + r * .24, cy + r * .4), (cx, cy + r * .46),
                 (cx - r * .24, cy + r * .4), (cx - r * .6, cy + r * .42)], col, 8)


def _flag_head(c, cx, cy, r, flag):
    bands = [rgba(x) for x in flag["bands"]]
    S = c.ss
    box = Image.new("RGBA", (2 * r * S, 2 * r * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    n = len(bands)
    for i, col in enumerate(bands):
        if flag.get("dir") == "v":
            d.rectangle((i * 2 * r * S // n, 0, (i + 1) * 2 * r * S // n, 2 * r * S), fill=col)
        else:
            d.rectangle((0, i * 2 * r * S // n, 2 * r * S, (i + 1) * 2 * r * S // n), fill=col)
    mask = Image.new("L", box.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, box.width - 1, box.height - 1), fill=255)
    box.putalpha(mask)
    c.im.alpha_composite(box, (int((cx - r) * S), int((cy - r) * S)))
    c.ellipse(cx, cy, r, r, None, 10)
    for s in (-1, 1):
        c.ellipse(cx + s * r * .36, cy, 16, 16, (255, 255, 255, 255), 6)
        c.ellipse(cx + s * r * .36, cy, 5, 5, INK, 0)


def _body(c, cx, top, h, spec, skin):
    robe = rgba(spec.get("robe", "#7a8a70"))
    w = h * .4
    c.shape([(cx - w * .62, top, 1), (cx + w * .62, top, 1), (cx + w * .8, top + h * .6), (cx + w * .96, top + h, 1),
             (cx - w * .96, top + h, 1), (cx - w * .8, top + h * .6)], robe, 10)
    c.line([(cx - w * .1, top), (cx + w * .36, top + h * .44)], 7)
    c.line([(cx + w * .1, top), (cx - w * .36, top + h * .44)], 7)
    if spec.get("sash"):
        s = rgba(spec["sash"])
        c.shape([(cx - w * .86, top + h * .52, 1), (cx + w * .86, top + h * .52, 1), (cx + w * .9, top + h * .64, 1),
                 (cx - w * .9, top + h * .64, 1)], s, 7, soft=False)
    if spec.get("cape"):
        k = rgba(spec["cape"])
        for sg in (-1, 1):
            c.shape([(cx + sg * w * .62, top, 1), (cx + sg * w * 1.06, top + h * .5), (cx + sg * w * 1.14, top + h, 1),
                     (cx + sg * w * .7, top + h, 1), (cx + sg * w * .4, top + h * .4)], k, 9)


def _hands(c, cx, top, h, pose, skin):
    w = h * .36
    if pose == "point":
        mitten(c, cx + w * 1.5, top + h * .36, "point", .9, False, skin, 8)
    elif pose == "fist":
        mitten(c, cx + w * 1.5, top + h * .3, "fist", .95, False, skin, 8)
    elif pose == "pray":
        mitten(c, cx, top + h * .26, "pray", .9, False, skin, 8)
    elif pose == "raised":
        mitten(c, cx + w * 1.44, top - h * .05, "open", .95, False, skin, 8)
    elif pose in ("think", "hand_chin"):
        mitten(c, cx + w * .3, top - h * .02, "fist", .8, False, skin, 8)
    elif pose == "cross":
        mitten(c, cx - w * .4, top + h * .3, "fist", .85, False, skin, 8)
        mitten(c, cx + w * .4, top + h * .34, "fist", .85, True, skin, 8)
    elif pose == "sword":
        x, y = cx + w * 1.5, top + h * .3
        c.shape([(x - 11, y - 20, 1), (x + 6, y - 248, 1), (x + 26, y - 262, 1), (x + 32, y - 20, 1)], (214, 222, 226, 255), 7, soft=False)
        c.line([(x - 36, y - 16), (x + 56, y - 22)], 11, (120, 88, 40, 255))
        mitten(c, x + 10, y + 8, "fist", .9, False, skin, 8)
    elif pose == "scroll":
        x, y = cx + w * 1.5, top + h * .3
        c.shape([(x - 54, y - 60, 1), (x + 54, y - 60, 1), (x + 54, y + 60, 1), (x - 54, y + 60, 1)], (232, 212, 170, 255), 7)
        mitten(c, x - 54, y + 42, "fist", .7, False, skin, 8)


@lru_cache(maxsize=1024)
def _draw(js, pose, expr, mouth):
    spec = json.loads(js)
    skin = SKIN.get(spec.get("skin", "light"), SKIN["light"])
    r = 150
    c = Canvas(760, 900)
    cx, cy = 380, 300
    hair_col = rgba(spec.get("hair_col", "#3a2a22"))
    hair = spec.get("hair", "short")
    beard_col = rgba(spec.get("beard_col", spec.get("hair_col", "#555050")))
    _hair_back(c, cx, cy, r, hair, hair_col)
    _body(c, cx, cy + r * .9, BODY, spec, skin)
    if spec.get("flag"):
        _flag_head(c, cx, cy, r, spec["flag"])
    else:
        c.ellipse(cx, cy + 4, r * 1.04, r * .98, skin, 10)
        c.ellipse(cx - r * 1.03, cy + 20, 18, 26, skin, 8)
        c.ellipse(cx + r * 1.03, cy + 20, 18, 26, skin, 8)
        _beard(c, cx, cy, r, spec.get("beard", "none"), beard_col)
        _face(c, cx, cy, r, expr, mouth, skin)
        if spec.get("beard") == "full" or spec.get("beard") == "long":
            c.line([(cx - 16, cy + r * .62), (cx + 16, cy + r * .62)], 6)
        _hair_front(c, cx, cy, r, hair, hair_col)
    h = spec.get("hat", "none")
    if h != "none":
        _hat(c, cx, cy, r, h, rgba(spec["hat_col"]) if spec.get("hat_col") else None)
    _hands(c, cx, cy + r * .9, BODY, pose, skin)
    return c.image()


def draw(spec, pose="idle", expr="normal", mouth="closed"):
    """760x900 sprite with the feet at the bottom edge area (see FEET)."""
    return _draw(json.dumps(spec, sort_keys=True, ensure_ascii=False), pose, expr, mouth)
