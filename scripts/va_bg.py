"""Procedural backgrounds: flat colour shapes, thin ink lines, watercolor + paper grain.
Each background is a function of a seed, so a place keeps its look across a video."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from PIL import Image

from va_draw import Canvas, INK, paper, rnd, textured, tint_night, vignette_gray

W, H = 1920, 1080
THIN = (40, 34, 30, 255)


def _paint(base, draw, seed):
    c = Canvas()
    draw(c)
    bg = paper(W, H, base, seed=seed)
    bg.alpha_composite(textured(c.image(), seed + 1))
    return bg


def _ground(c, y, col, r):
    c.shape([(0, y, 1), *[(x, y + r.randint(-10, 10)) for x in range(160, 1800, 240)], (W, y, 1), (W, H, 1), (0, H, 1)], col, 3, THIN)


def mountains(seed):
    r = rnd(seed)

    def d(c):
        c.shape([(0, 300, 1), (300, 180), (660, 60), (1000, 170), (1400, 300), (1900, 80), (1920, 90, 1), (1920, 640, 1), (0, 640, 1)],
                (132, 146, 150, 255), 3, THIN)
        for x, y in ((560, 470), (1060, 400), (1560, 420)):
            c.shape([(x - 180, y + 90, 1), (x - 60, y + 20), (x, y - 40), (x + 90, y - 80), (x + 40, y + 10), (x - 40, y + 60)],
                    (250, 250, 248, 255), 0)
        c.shape([(0, 500), (100, 490), (220, 575, 1), (0, 580, 1)], (146, 170, 130, 255), 2, THIN)
        c.shape([(1920, 440), (1780, 460), (1660, 530), (1600, 575, 1), (1920, 580, 1)], (146, 170, 130, 255), 2, THIN)
        _ground(c, 578, (168, 148, 134, 255), r)
    return _paint((186, 224, 226), d, seed)


def field(seed):
    r = rnd(seed)

    def d(c):
        for cx in (360, 1300):
            c.shape([(cx - 240, 250), (cx - 130, 170), (cx, 200), (cx + 130, 150), (cx + 260, 250)], (252, 252, 250, 255), 0)
        c.shape([(0, 480, 1), (260, 380), (640, 460), (1000, 370), (1500, 470), (1920, 390), (1920, 700, 1), (0, 700, 1)], (156, 200, 150, 255), 2, THIN)
        _ground(c, 620, (170, 212, 122, 255), r)
        for _ in range(24):
            x, y = r.randint(40, 1880), r.randint(660, 1040)
            c.line([(x, y), (x + 5, y - 16)], 2, THIN)
            c.line([(x + 12, y), (x + 14, y - 12)], 2, THIN)
    return _paint((198, 232, 246), d, seed)


def forest(seed):
    r = rnd(seed)

    def d(c):
        c.shape([(0, 500, 1), (400, 430), (900, 500), (1400, 420), (1920, 500, 1), (1920, 700, 1), (0, 700, 1)], (178, 216, 170, 255), 0)
        for i in range(12):
            x = 60 + i * 165 + r.randint(-40, 40)
            w = r.randint(16, 34)
            k = (146 + r.randint(-16, 16), 112 + r.randint(-12, 12), 88, 255)
            c.shape([(x - w, 0, 1), (x + w, 0, 1), (x + w * 1.6, 760, 1), (x - w * 1.6, 760, 1)], k, 3, THIN, soft=False)
        _ground(c, 730, (150, 192, 104, 255), r)
    return _paint((214, 238, 216), d, seed)


def desert(seed):
    r = rnd(seed)

    def d(c):
        c.ellipse(1560, 170, 90, 90, (252, 226, 110, 255), 0)
        c.shape([(0, 620, 1), (340, 540), (820, 640), (1240, 530), (1920, 620, 1), (1920, 760, 1), (0, 760, 1)], (238, 206, 132, 255), 2, THIN)
        _ground(c, 700, (246, 214, 124, 255), r)
        for x in (150, 1760):
            c.shape([(x - 12, 720, 1), (x + 6, 460), (x + 26, 720, 1)], (150, 110, 70, 255), 3, THIN)
            for a in (-110, -60, 60, 110):
                c.shape([(x + 6, 455), (x + 6 + a, 400), (x + 6 + a * 1.5, 470), (x + 6 + a * .6, 440)], (98, 172, 92, 255), 3, THIN)
    return _paint((142, 220, 244), d, seed)


def wall_room(seed, wall=(232, 220, 196), floor=(186, 140, 104)):
    r = rnd(seed)

    def d(c):
        c.rect(0, 720, 1920, 1080, (*floor, 255), 3, THIN)
        for x in range(0, 1920, 240):
            c.line([(x, 722), (x - 60, 1080)], 2, THIN)
        c.rect(0, 690, 1920, 724, (150, 112, 84, 255), 3, THIN)
        for x in (420, 1260):
            c.rect(x, 170, x + 240, 520, (196, 232, 246, 255), 6, THIN)
            c.line([(x + 120, 170), (x + 120, 520)], 4, THIN)
            c.line([(x, 345), (x + 240, 345)], 4, THIN)
    return _paint(wall, d, seed)


def office(seed):
    return wall_room(seed, wall=(150, 182, 160), floor=(206, 208, 200))


def throne(seed):
    def d(c):
        c.rect(0, 0, 1920, 760, (104, 106, 104, 255), 3, THIN)
        c.rect(640, 0, 1280, 620, (140, 22, 50, 255), 3, THIN)
        for x in range(700, 1280, 90):
            c.line([(x, 0), (x + 6, 620)], 3, (92, 12, 34, 255))
        for i, y in enumerate((760, 840, 930)):
            k = (232, 186, 66, 255)
            c.shape([(180 - i * 90, y, 1), (1740 + i * 90, y, 1), (1800 + i * 110, y + 80, 1), (120 - i * 110, y + 80, 1)], k, 3, THIN, soft=False)
        c.shape([(560, 640, 1), (1360, 640, 1), (1800, 1080, 1), (120, 1080, 1)], (156, 28, 52, 255), 3, THIN, soft=False)
        c.rect(780, 330, 1140, 680, (120, 40, 60, 255), 8)
        c.rect(740, 620, 1180, 700, (216, 170, 56, 255), 8)
    return _paint((186, 180, 170), d, seed)


def palace(seed):
    def d(c):
        c.rect(0, 660, 1920, 1080, (246, 238, 196, 255), 3, THIN)
        c.shape([(640, 660, 1), (1280, 660, 1), (1620, 1080, 1), (300, 1080, 1)], (230, 190, 170, 255), 3, THIN, soft=False)
        for x in range(120, 1800, 420):
            c.rect(x, 0, x + 56, 660, (232, 226, 150, 255), 4, THIN)
        for x in range(176, 1600, 420):
            c.shape([(x, 660, 1), (x, 200), (x + 182, 80), (x + 364, 200), (x + 364, 660, 1)], (252, 248, 218, 255), 4, THIN)
    return _paint((252, 248, 222), d, seed)


def hut(seed):
    """Round-door hillside cottage."""
    r = rnd(seed)

    def d(c):
        c.shape([(20, 420, 1), (500, 240), (960, 130), (1420, 240), (1900, 450, 1), (1900, 610, 1), (20, 610, 1)], (234, 220, 204, 255), 3, THIN)
        c.line([(20, 420), (500, 240), (960, 130), (1420, 240), (1900, 450)], 24, (120, 76, 44, 255))
        c.shape([(780, 590, 1), (780, 330), (960, 230), (1140, 330), (1140, 590, 1)], (190, 180, 164, 255), 3, THIN)
        c.shape([(810, 590, 1), (810, 350), (960, 280), (1110, 350), (1110, 590, 1)], (206, 150, 92, 255), 3, THIN)
        for x in (430, 1380):
            c.shape([(x, 480, 1), (x, 370), (x + 110, 310), (x + 220, 370), (x + 220, 480, 1)], (190, 180, 164, 255), 3, THIN)
            c.ellipse(x + 40, 520, 70, 70, (106, 158, 72, 255), 3, THIN)
        c.shape([(620, 1080, 1), (760, 600), (1160, 600), (1500, 1080, 1)], (190, 176, 160, 255), 3, THIN)
        for _ in range(14):
            x, y = r.randint(30, 1880), r.randint(30, 200)
            c.line([(x, y), (x + 5, y - 14)], 2, THIN)
    return _paint((164, 210, 110), d, seed)


def tents(seed):
    r = rnd(seed)

    def d(c):
        c.shape([(0, 460, 1), (500, 400), (1100, 450), (1920, 390, 1), (1920, 560, 1), (0, 560, 1)], (190, 208, 192, 255), 0)
        _ground(c, 540, (206, 196, 170, 255), r)
        for x, s in ((280, .7), (1560, .8), (640, .6), (1240, .6), (960, 1.3)):
            c.shape([(x - 180 * s, 560, 1), (x - 190 * s, 440), (x - 60 * s, 370), (x, 300 - 40 * s, 1), (x + 60 * s, 370), (x + 190 * s, 440), (x + 180 * s, 560, 1)],
                    (226, 230, 226, 255), 3, THIN)
    return _paint((206, 232, 232), d, seed)


def river(seed):
    r = rnd(seed)

    def d(c):
        c.shape([(0, 430, 1), (360, 340), (800, 420), (1200, 330), (1920, 430, 1), (1920, 560, 1), (0, 560, 1)], (170, 196, 164, 255), 2, THIN)
        c.rect(0, 540, 1920, 1080, (178, 216, 226, 255), 0)
        for _ in range(26):
            x, y = r.randint(20, 1800), r.randint(590, 1050)
            c.line([(x, y), (x + r.randint(30, 80), y)], 2, (250, 250, 250, 255))
    return _paint((206, 232, 238), d, seed)


def castle(seed):
    r = rnd(seed)

    def d(c):
        for x in (300, 1260):
            c.rect(x, 340, x + 360, 700, (182, 174, 170, 255), 4, THIN)
            for i in range(5):
                c.rect(x + i * 80, 300, x + i * 80 + 46, 342, (182, 174, 170, 255), 4, THIN)
        c.rect(660, 450, 1260, 700, (172, 160, 156, 255), 4, THIN)
        c.shape([(900, 700, 1), (900, 580), (960, 530), (1020, 580), (1020, 700, 1)], (112, 76, 60, 255), 4, THIN)
        _ground(c, 690, (246, 214, 124, 255), r)
    return _paint((142, 220, 244), d, seed)


def dungeon(seed):
    def d(c):
        for y in range(0, 1080, 90):
            c.line([(0, y), (1920, y)], 2, (60, 56, 96, 255))
            for x in range((y // 90 % 2) * 110, 1920, 220):
                c.line([(x, y), (x, y + 90)], 2, (60, 56, 96, 255))
        c.rect(760, 220, 1160, 900, (60, 48, 70, 255), 6, THIN)
        for x in range(820, 1160, 70):
            c.line([(x, 222), (x, 898)], 5, (34, 28, 40, 255))
    return _paint((116, 112, 170), d, seed)


def white(seed=0):
    return Image.new("RGBA", (W, H), (254, 254, 252, 255))


def parchment(seed=2):
    im = paper(W, H, (246, 226, 186), grain=3.0, blotch=3.5, seed=seed)
    a = np.asarray(im, np.float32).copy()
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.maximum(np.abs(xx - W / 2) / (W / 2), np.abs(yy - H / 2) / (H / 2))
    a[..., :3] *= (1 - .16 * (np.clip(r - .9, 0, 1) / .1) ** 2)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


NAMES = {"white": white, "parchment": parchment, "mountains": mountains, "field": field, "forest": forest,
         "desert": desert, "room": wall_room, "office": office, "throne": throne, "palace": palace, "hut": hut,
         "tents": tents, "river": river, "castle": castle, "dungeon": dungeon}


@lru_cache(maxsize=64)
def get(name, seed=1, mood="day"):
    im = NAMES[name](seed)
    if mood == "gray":
        return vignette_gray(im)
    if mood == "night":
        return tint_night(im)
    return im
