"""Drawing primitives for the video-anime style: thick round ink outline, flat colour,
paper grain. Everything is drawn in 1920x1080 coordinates and supersampled."""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
INK = (18, 16, 18, 255)
SS = 2


def smooth(pts, closed=True, steps=10):
    """Catmull-Rom through pts. A point given as (x, y, 1) stays a sharp corner."""
    corners = [len(p) > 2 and p[2] for p in pts]
    P = [(p[0], p[1]) for p in pts]
    n = len(P)
    out = []
    for i in range(n if closed else n - 1):
        p0 = P[(i - 1) % n] if closed or i > 0 else P[i]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if closed or i + 2 < n else p2
        if corners[i]:
            p0 = p1
        if corners[(i + 1) % n]:
            p3 = p2
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (p2[j] - p0[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (3 * p1[j] - p0[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not closed:
        out.append(P[-1])
    return out


class Canvas:
    """RGBA drawing surface; call .image() for the antialiased result."""

    def __init__(self, w=1920, h=1080, ss=SS):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _s(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def stroke(self, pts, lw=10, color=INK):
        pts = self._s(pts)
        w = int(lw * self.ss)
        self.d.line(pts, fill=color, width=w, joint="curve")
        r = w / 2
        for x, y in pts[:: max(1, len(pts) // 60)] + [pts[-1]]:
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def shape(self, pts, fill=None, lw=10, color=INK, soft=True, closed=True):
        path = smooth(pts, closed) if soft else [(p[0], p[1]) for p in pts]
        if fill is not None:
            self.d.polygon(self._s(path), fill=fill)
        if lw:
            self.stroke(path + ([path[0]] if closed else []), lw, color)

    def line(self, pts, lw=10, color=INK, soft=True):
        self.stroke(smooth(pts, False) if soft and len(pts) > 2 else [(p[0], p[1]) for p in pts], lw, color)

    def ellipse(self, cx, cy, rx, ry, fill=None, lw=10, color=INK, rot=0):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        path = [(cx + rx * math.cos(a) * c - ry * math.sin(a) * s, cy + rx * math.cos(a) * s + ry * math.sin(a) * c)
                for a in np.linspace(0, 2 * math.pi, 72)]
        self.shape(path, fill, lw, color, soft=False)

    def rect(self, x0, y0, x1, y1, fill=None, lw=6, color=INK):
        self.shape([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, lw, color, soft=False)

    def image(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS) if self.ss > 1 else self.im.copy()


def mitten(c, x, y, kind="open", s=1.0, flip=False, skin=(254, 234, 226, 255), lw=9):
    """The floating hands of the style: open palm, point, fist, thumb, ok, pray."""
    f = -1 if flip else 1

    def P(u, v, corner=False):
        return (x + f * u * s, y + v * s, 1) if corner else (x + f * u * s, y + v * s)
    if kind == "fist":
        c.shape([P(-34, -8), P(-16, -36), P(20, -34), P(38, -6), P(26, 28), P(-18, 30)], skin, lw)
        c.line([P(-6, -34), P(-2, -6)], lw * .7)
        c.line([P(14, -30), P(16, -4)], lw * .7)
    elif kind == "thumb":
        c.shape([P(-30, 2), P(-14, -18), P(-2, -14), P(4, -66), P(20, -68), P(26, -14), P(32, 20), P(4, 40), P(-22, 30)], skin, lw)
        c.line([P(-20, 8), P(4, 2)], lw * .7)
        c.line([P(-16, 22), P(6, 18)], lw * .7)
    elif kind == "point":
        c.shape([P(-30, -18), P(10, -24), P(66, -22), P(70, -8), P(24, -2), P(30, 24), P(-8, 34), P(-34, 12)], skin, lw)
        c.line([P(-4, 6), P(22, 4)], lw * .7)
    elif kind == "ok":
        c.ellipse(x - f * 12 * s, y, 20 * s, 18 * s, skin, lw)
        c.shape([P(0, -20), P(14, -44), P(30, -36), P(22, -8), P(30, 14), P(6, 26), P(-14, 18)], skin, lw)
        c.ellipse(x - f * 12 * s, y, 9 * s, 8 * s, (255, 255, 255, 0), lw * .7)
    elif kind == "pray":
        c.shape([P(-14, 40), P(-22, -8), P(0, -48), P(22, -8), P(14, 40)], skin, lw)
        c.line([P(0, -44), P(0, 36)], lw * .7)
    else:  # open palm, slightly cupped
        c.shape([P(-36, 10), P(-26, -22), P(-4, -14), P(18, -28), P(40, -26), P(34, -8), P(46, 2), P(26, 26), P(-16, 30)], skin, lw)


def font(size, kind="hand"):
    name = {"hand": "PatrickHand-Regular.ttf", "round": "Pangolin-Regular.ttf", "bold": "Itim-Regular.ttf"}[kind]
    return ImageFont.truetype(str(FONTS / name), size)


def text_outlined(size_wh, text, xy, size=64, fill=(20, 18, 20, 255), outline=None, ow=8, kind="hand", anchor="mm"):
    """Returns an RGBA layer. outline=(r,g,b,a) gives the sticker look of the labels."""
    im = Image.new("RGBA", size_wh, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(size, kind)
    d.multiline_text(xy, text, font=f, fill=fill, anchor=anchor, align="center", spacing=8,
                     stroke_width=ow if outline else 0, stroke_fill=outline)
    return im


def paper(w, h, base, grain=2.4, blotch=4.5, seed=1):
    """Flat colour + watercolor blotches + fine grain: the texture of every background."""
    rng = np.random.default_rng(seed)
    a = np.ones((h, w, 3), np.float32) * np.array(base[:3], np.float32)
    lo = rng.normal(0, 1, (h // 180 + 3, w // 180 + 3)).astype(np.float32)
    lo = np.asarray(Image.fromarray(lo).resize((w, h), Image.BICUBIC))
    a += (lo * blotch)[..., None]
    a += rng.normal(0, grain, (h, w, 1)).astype(np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def textured(mask_layer, seed=3):
    """Apply a light watercolor variation to a flat layer (keeps its alpha)."""
    w, h = mask_layer.size
    rng = np.random.default_rng(seed)
    lo = rng.normal(0, 1, (h // 140 + 3, w // 140 + 3)).astype(np.float32)
    lo = np.asarray(Image.fromarray(lo).resize((w, h), Image.BICUBIC)) * 4 + rng.normal(0, 1.8, (h, w)).astype(np.float32)
    a = np.asarray(mask_layer, np.float32).copy()
    a[..., :3] = np.clip(a[..., :3] + lo[..., None], 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def over(dst, src, xy=(0, 0)):
    dst.alpha_composite(src, (int(xy[0]), int(xy[1])))
    return dst


def fit_cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def fit_contain(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def vignette_gray(im, strength=.62):
    """The B/W flashback of the samples: desaturated, dark corners."""
    a = np.asarray(im.convert("RGB"), np.float32)
    g = a @ np.array([.3, .59, .11], np.float32)
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    g = g * (1 - strength * np.clip(r - .45, 0, 1) ** 1.4)
    return Image.fromarray(np.clip(np.dstack([g, g, g]), 0, 255).astype(np.uint8)).convert("RGBA")


def tint_night(im):
    a = np.asarray(im.convert("RGB"), np.float32) * np.array([.42, .42, .62], np.float32)
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def rnd(seed):
    return random.Random(seed)
