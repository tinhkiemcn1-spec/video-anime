"""The host ("nhân vật trụ"): tall pentagon head, spiky hair, stick legs, cross-body bag.
Coordinates were measured on a 1080p sample frame; the sprite is 1000x1100 with origin at
the hip (500, 760). Colours come from a preset, so the character can be re-skinned."""
from __future__ import annotations

from functools import lru_cache

from PIL import Image

from va_draw import Canvas, INK, mitten

PRESETS = {
    # same construction as the sample's character
    "mau": {"hair": (211, 92, 128, 255), "skin": (254, 234, 226, 255), "shirt": (252, 208, 124, 255),
            "bag": (69, 49, 112, 255), "shine": (222, 96, 140, 255), "red": (160, 8, 24, 255)},
    # original palette for a channel of your own
    "goc": {"hair": (58, 158, 150, 255), "skin": (254, 234, 226, 255), "shirt": (240, 130, 84, 255),
            "bag": (38, 62, 96, 255), "shine": (92, 200, 190, 255), "red": (160, 8, 24, 255)},
}

POSES = ("idle", "thumb", "point_up", "present", "point", "shrug", "ok", "think", "read", "hip")
EYES = ("line", "closed", "wide", "happy", "shut")
BROWS = ("none", "up", "angry", "worried")
MOUTHS = ("closed", "small", "open", "wide", "smile", "smirk", "frown", "laugh")


def _face(c, ox, oy, s, eyes, brow, mouth, col):
    def X(u):
        return ox + u * s

    def Y(v):
        return oy + v * s
    lw = 8 * s
    if eyes == "line":
        for u in (-58, 62):
            c.line([(X(u), Y(-30)), (X(u + 2), Y(30))], 8 * s)
    elif eyes == "closed":
        for u in (-62, 62):
            c.line([(X(u - 32), Y(-6)), (X(u), Y(10)), (X(u + 32), Y(-8))], lw)
    elif eyes == "happy":
        for u in (-62, 62):
            c.line([(X(u - 30), Y(10)), (X(u), Y(-14)), (X(u + 30), Y(10))], lw)
    elif eyes == "shut":
        for u in (-62, 62):
            c.line([(X(u - 26), Y(0)), (X(u + 26), Y(0))], lw)
    else:  # wide = smug white ovals
        for u in (-62, 66):
            c.ellipse(X(u), Y(0), 42 * s, 20 * s, (255, 255, 255, 255), 7 * s)
            c.ellipse(X(u + 8), Y(0), 7 * s, 7 * s, INK, 0)
    if brow == "angry":
        c.line([(X(-96), Y(-74)), (X(-66), Y(-82)), (X(-36), Y(-50))], lw)
        c.line([(X(94), Y(-74)), (X(66), Y(-82)), (X(36), Y(-50))], lw)
    elif brow == "up":
        c.line([(X(-90), Y(-70)), (X(-62), Y(-86)), (X(-34), Y(-70))], lw)
        c.line([(X(38), Y(-72)), (X(66), Y(-88)), (X(92), Y(-72))], lw)
    elif brow == "worried":
        c.line([(X(-92), Y(-54)), (X(-62), Y(-76)), (X(-34), Y(-80))], lw)
        c.line([(X(92), Y(-54)), (X(62), Y(-76)), (X(34), Y(-80))], lw)
    mx, my = X(4), Y(82)
    if mouth == "closed":
        c.line([(mx - 26 * s, my), (mx + 26 * s, my)], lw)
    elif mouth == "small":
        c.ellipse(mx, my, 15 * s, 13 * s, col["red"], lw)
    elif mouth == "open":
        c.ellipse(mx, my, 22 * s, 32 * s, col["red"], lw)
    elif mouth == "wide":
        c.shape([(mx - 42 * s, my - 18 * s, 1), (mx + 42 * s, my - 20 * s, 1), (mx, my + 36 * s)], col["red"], lw)
    elif mouth == "laugh":
        c.shape([(mx - 54 * s, my - 22 * s, 1), (mx + 54 * s, my - 24 * s, 1), (mx, my + 46 * s)], col["red"], lw)
    elif mouth == "smile":
        c.line([(mx - 36 * s, my - 6 * s), (mx, my + 14 * s), (mx + 36 * s, my - 8 * s)], lw)
    elif mouth == "smirk":
        c.line([(mx - 30 * s, my + 4 * s), (mx + 4 * s, my + 8 * s), (mx + 40 * s, my - 14 * s)], lw)
    elif mouth == "frown":
        c.line([(mx - 32 * s, my + 12 * s), (mx, my - 4 * s), (mx + 32 * s, my + 12 * s)], lw)


def _head(c, cx, cy, tilt, eyes, brow, mouth, glasses, col):
    # the pentagon from the sample, relative to its visual centre
    def R(u, v):
        import math
        a = math.radians(tilt)
        return (cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a))
    head = [R(-152, -118), R(158, -102), R(112, 112), R(-38, 182), R(-164, 106)]
    c.shape([(*p, 1) for p in head], col["skin"], 13)
    # side burn panel + spiky hair
    side = [R(158, -104), R(98, -92), R(120, 62), R(146, -20)]
    c.shape([(*p, 1) for p in side], col["hair"], 0)
    hair = [R(-150, -118), R(-188, -176), R(-196, -196), R(-176, -216), R(-150, -222),
            R(-162, -252), R(-126, -252), R(-74, -228), R(-98, -256), R(-64, -258), R(-16, -232),
            R(-38, -266), R(-4, -268), R(48, -240), R(112, -200), R(118, -226), R(150, -196),
            R(186, -140), R(198, -94), R(160, -100)]
    corners = {0, 3, 4, 7, 10, 13, 14, 15, 19}
    c.shape([(*p, 1) if i in corners else p for i, p in enumerate(hair)], col["hair"], 13)
    c.line([R(-150, -116), R(-24, -112), R(100, -96)], 0)
    c.shape([(*R(-44, -116), 1), (*R(-58, -142), 1), (*R(-36, -124), 1), (*R(-30, -142), 1), (*R(-16, -112), 1)],
            (250, 214, 214, 255), 0, soft=False)
    _face(c, cx - 8, cy - 6, 1.0, eyes, brow, mouth, col)
    if glasses:
        for u in (-62, 62):
            c.ellipse(cx - 8 + u, cy - 4, 48, 48, None, 7)
        c.line([(cx - 22, cy - 6), (cx + 6, cy - 6)], 7)


def _body(c, cx, top, col, legs=True):
    if legs:
        for x0, y0, x1, y1, fx, fy, r in ((cx - 62, top + 210, cx - 44, top + 355, cx - 86, top + 392, 8),
                                          (cx + 56, top + 210, cx + 84, top + 370, cx + 64, top + 425, -30)):
            c.line([(x0, y0), (x0 + (x1 - x0) * .5, top + 290), (x1, y1)], 9)
            c.ellipse(fx, fy, 46, 30, col["skin"], 10, rot=r)
    body = [(cx - 52, top, 1), (cx + 72, top, 1), (cx + 128, top + 214, 1), (cx + 20, top + 232), (cx - 84, top + 214, 1)]
    c.shape(body, col["shirt"], 13)
    # bag + strap
    c.line([(cx - 38, top + 16), (cx + 22, top + 100)], 26)
    c.line([(cx - 38, top + 16), (cx + 22, top + 100)], 12, col["bag"])
    c.line([(cx + 60, top + 150), (cx + 118, top + 170)], 26)
    c.line([(cx + 60, top + 150), (cx + 118, top + 170)], 12, col["bag"])
    c.ellipse(cx + 44, top + 128, 56, 62, col["bag"], 11, rot=-44)
    c.line([(cx + 16, top + 104), (cx + 60, top + 130)], 8, col["shine"])


def _arm(c, pts, kind, s, col, flip=False):
    c.line(pts, 10)
    x, y = pts[-1]
    mitten(c, x, y, kind, s, flip, col["skin"], 9)


@lru_cache(maxsize=512)
def draw(pose="idle", eyes="line", brow="none", mouth="closed", sway=0, close=False, preset="mau"):
    """1000x1100 sprite. close=True is the waist-up framing the samples cut to for reactions."""
    col = PRESETS[preset]
    c = Canvas(1000, 1100)
    cx, top = 480, 560
    tilt = sway * .9
    behind = pose in ("shrug",)
    if pose in ("idle", "hip"):
        c.line([(cx + 66, top + 8), (cx + 150, top + 76), (cx + 120, top + 140)], 10)
        c.line([(cx - 44, top + 8), (cx - 120, top + 70), (cx - 70, top + 130)], 10)
    if behind:
        _arm(c, [(cx - 44, top + 40), (cx - 150, top + 110), (cx - 240, top + 60)], "open", 1.0, col, True)
        _arm(c, [(cx + 70, top + 40), (cx + 190, top + 110), (cx + 270, top + 50)], "open", 1.0, col)
    _body(c, cx, top, col)
    if pose == "thumb":
        c.line([(cx + 72, top + 10), (cx + 150, top + 76), (cx + 118, top + 140)], 10)
        _arm(c, [(cx - 44, top + 8), (cx - 120, top + 110), (cx - 170, top - 10)], "thumb", 1.1, col, True)
    elif pose == "point_up":
        c.line([(cx + 72, top + 10), (cx + 150, top + 76), (cx + 118, top + 140)], 10)
        _arm(c, [(cx - 44, top + 8), (cx - 110, top + 96), (cx - 150, top - 30)], "thumb", .9, col, True)
    elif pose in ("present", "point"):
        c.line([(cx + 72, top + 10), (cx + 150, top + 76), (cx + 118, top + 140)], 10)
        _arm(c, [(cx - 44, top + 12), (cx - 130, top + 82), (cx - 220, top + 30)],
             "open" if pose == "present" else "point", 1.0, col, True)
    elif pose == "ok":
        c.line([(cx + 72, top + 10), (cx + 150, top + 76), (cx + 118, top + 140)], 10)
        _arm(c, [(cx - 44, top + 12), (cx - 110, top + 100), (cx - 170, top + 10)], "ok", 1.1, col, True)
    elif pose == "think":
        _arm(c, [(cx - 44, top + 12), (cx - 90, top + 110), (cx - 6, top - 6)], "fist", .95, col)
    elif pose == "read":
        c.shape([(cx - 30, top + 40, 1), (cx + 150, top - 40, 1), (cx + 160, top + 150, 1), (cx - 20, top + 210, 1)],
                (108, 146, 160, 255), 10)
        c.shape([(cx + 150, top - 40, 1), (cx + 186, top - 76, 1), (cx + 196, top + 110, 1), (cx + 160, top + 150, 1)],
                (84, 120, 136, 255), 10)
        mitten(c, cx - 24, top + 170, "fist", .8, False, col["skin"], 9)
    _head(c, cx + 6, top - 196, tilt, eyes, brow, mouth, pose == "read", col)
    im = c.image()
    if close:
        s = 1.7
        im = im.resize((int(1000 * s), int(1100 * s)), Image.LANCZOS)
    return im
