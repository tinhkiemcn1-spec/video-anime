"""Synthesize the small SFX kit into assets/sfx (48 kHz, royalty free because it is generated)."""
from pathlib import Path
import wave

import numpy as np

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def save(name, y):
    y = y / (np.abs(y).max() + 1e-9) * .85
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


x = t(.12)
save("pop", np.sin(2 * np.pi * (900 - 5000 * x) * x) * np.exp(-x * 40))
x = t(.45)
n = rng.normal(0, 1, len(x))
f = np.cumsum(n) - np.convolve(np.cumsum(n), np.ones(40) / 40, "same")
save("whoosh", f * np.sin(np.pi * x / .45) ** 2)
x = t(.9)
save("ding", (np.sin(2 * np.pi * 1320 * x) + .5 * np.sin(2 * np.pi * 2640 * x)) * np.exp(-x * 5))
x = t(.5)
save("boing", np.sin(2 * np.pi * (180 + 90 * np.sin(2 * np.pi * 9 * x)) * x) * np.exp(-x * 5))
x = t(.3)
save("thud", (np.sin(2 * np.pi * 70 * x) + .3 * rng.normal(0, 1, len(x)) * np.exp(-x * 60)) * np.exp(-x * 14))
x = t(.25)
save("tick", np.sin(2 * np.pi * 2000 * x) * np.exp(-x * 90))
x = t(.7)
save("fail", np.concatenate([np.sin(2 * np.pi * h * t(.22)) * np.exp(-t(.22) * 5) for h in (392, 370, 330)]))
print("sfx written to", OUT)
