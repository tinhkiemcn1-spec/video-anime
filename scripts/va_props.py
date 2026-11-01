"""Props and overlays: TV on desk, speech bubbles, marks, name badges, map circles."""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from va_draw import Canvas, INK, fit_cover, font, text_outlined

RED = (232, 16, 36, 255)


def tv_desk(screen=None):
    """Full frame desk + monitor; screen is an RGB(A) image shown on it (the recap device)."""
    c = Canvas()
    wood, dark = (126, 100, 88, 255), (102, 76, 66, 255)
    for x0, x1 in ((270, 330), (1600, 1660)):
        c.rect(x0, 790, x1, 1090, wood, 8)
    for x0, x1 in ((395, 455), (1475, 1530)):
        c.rect(x0, 800, x1, 950, dark, 8)
    c.shape([(340, 580, 1), (1590, 580, 1), (1700, 725, 1), (220, 725, 1)], wood, 8, soft=False)
    c.rect(220, 725, 1704, 765, dark, 8)
    c.rect(245, 765, 1680, 790, dark, 6)
    c.shape([(690, 550, 1), (730, 550, 1), (735, 590, 1), (870, 620, 1), (870, 640, 1), (545, 640, 1), (545, 620, 1), (685, 590, 1)],
            (44, 42, 62, 255), 8, soft=False)
    c.rect(388, 162, 1032, 553, (44, 42, 62, 255), 9)
    im = c.image()
    if screen is not None:
        im.alpha_composite(fit_cover(screen.convert("RGBA"), 566, 326), (428, 194))
    return im


def bubble(text=None, img=None, x=960, y=300, w=420, h=280, kind="speech", tail=(-1, 1)):
    """kind: speech | think | shout. The three bubble types of the samples, full-frame RGBA."""
    c = Canvas()
    tx, ty = x + tail[0] * w * .46, y + tail[1] * h * .62
    white = (255, 255, 255, 255)
    if kind == "shout":
        n = 13
        pts = []
        for i in range(n * 2):
            a = 2 * math.pi * i / (n * 2)
            k = 1.0 if i % 2 == 0 else .78
            pts.append((x + w / 2 * k * math.cos(a), y + h / 2 * k * math.sin(a), 1))
        c.shape(pts, white, 8, soft=False)
    elif kind == "think":
        pts = [(x + w / 2 * (1 + .1 * math.cos(9 * a)) * math.cos(a), y + h / 2 * (1 + .1 * math.cos(9 * a)) * math.sin(a))
               for a in [2 * math.pi * i / 36 for i in range(36)]]
        c.shape(pts, white, 8)
        for k, r in ((.0, 22), (.5, 15), (1.0, 9)):
            c.ellipse(x + tail[0] * w * (.52 + k * .12), y + tail[1] * h * (.62 + k * .22), r, r * .8, white, 7)
    else:
        c.ellipse(x, y, w / 2, h / 2, white, 8)
        c.shape([(x + tail[0] * w * .2, y + tail[1] * h * .4, 1), (tx, ty, 1), (x + tail[0] * w * .36, y + tail[1] * h * .24, 1)], white, 8, soft=False)
        c.shape([(x + tail[0] * w * .19, y + tail[1] * h * .36, 1), (x + tail[0] * w * .38, y + tail[1] * h * .2, 1),
                 (tx - tail[0] * 16, ty - tail[1] * 16, 1)], white, 0, soft=False)
    im = c.image()
    if img is not None:
        p = img.convert("RGBA")
        s = min(w * .62 / p.width, h * .62 / p.height)
        p = p.resize((round(p.width * s), round(p.height * s)), Image.LANCZOS)
        im.alpha_composite(p, (x - p.width // 2, y - p.height // 2))
    if text:
        size = 56 if len(text) < 26 else 44
        im.alpha_composite(text_outlined((1920, 1080), text, (x, y), size))
    return im


def mark(kind, x, y, s=1.0):
    """Manga marks: anger, sweat, !!!, ???, x (the big red cross), stars, lines."""
    c = Canvas()
    if kind == "x":
        L = 300 * s
        c.line([(x - L, y - L * .8), (x, y), (x + L, y + L * .8)], 62 * s, RED, soft=False)
        c.line([(x + L, y - L * .8), (x, y), (x - L, y + L * .8)], 62 * s, RED, soft=False)
    elif kind == "anger":
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            c.line([(x + dx * 34 * s, y + dy * 10 * s), (x + dx * 12 * s, y + dy * 12 * s), (x + dx * 10 * s, y + dy * 34 * s)], 13 * s, RED)
    elif kind == "sweat":
        c.shape([(x, y - 34 * s), (x - 22 * s, y + 14 * s), (x, y + 34 * s), (x + 22 * s, y + 14 * s)], (110, 188, 240, 255), 7 * s)
    elif kind == "laugh":
        for dx, dy in ((-46, -20), (46, -40)):
            c.line([(x + dx * s - 12 * s, y + dy * s), (x + dx * s + 12 * s, y + dy * s)], 7 * s)
            c.line([(x + dx * s - 8 * s, y + dy * s - 10 * s), (x + dx * s - 8 * s, y + dy * s + 10 * s)], 7 * s)
            c.line([(x + dx * s + 8 * s, y + dy * s - 10 * s), (x + dx * s + 8 * s, y + dy * s + 10 * s)], 7 * s)
    im = c.image()
    if kind in ("!!!", "???"):
        im.alpha_composite(text_outlined((1920, 1080), kind, (x, y), int(72 * s), kind="bold"))
    return im


def badge(img, text, d=420, bg=(84, 236, 206, 255)):
    """Round portrait + caption, the list-recap card. Returns RGBA 520x620."""
    S = 2
    im = Image.new("RGBA", (d * S, d * S), bg)
    if img is not None:
        p = img.convert("RGBA")
        if p.size == (760, 900):  # cast sprite: head and shoulders only
            p = p.crop((100, 60, 660, 620))
        s = max(d * S / p.width, d * S / p.height)
        p = p.resize((round(p.width * s), round(p.height * s)), Image.LANCZOS)
        im.alpha_composite(p, ((d * S - p.width) // 2, (d * S - p.height) // 2))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, im.width - 1, im.height - 1), fill=255)
    im.putalpha(m)
    ImageDraw.Draw(im).ellipse((0, 0, im.width - 1, im.height - 1), outline=INK, width=16)
    out = Image.new("RGBA", (520, 620), (0, 0, 0, 0))
    out.alpha_composite(im.resize((d, d), Image.LANCZOS), ((520 - d) // 2, 0))
    d2 = ImageDraw.Draw(out)
    d2.multiline_text((260, d + 86), text, font=font(52, "round"), fill=(20, 18, 20, 255), anchor="mm", align="center", spacing=6)
    return out


def ring(x, y, r, color=RED):
    c = Canvas()
    c.ellipse(x, y, r, r * .9, None, 7, color)
    return c.image()
