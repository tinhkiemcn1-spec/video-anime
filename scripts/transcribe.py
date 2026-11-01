"""VO -> <edit>/transcript.json: word times + sentences timed for shot planning.

    python -X utf8 transcribe.py <vo> <edit> [--model large-v3] [--prompt "tên riêng ..."] [--lang vi]

GPU when it really works, otherwise CPU (a CUDA card without cublas loads the model fine and
only fails at the first encode, so the fallback has to wrap the transcription itself).
Audio goes through ffmpeg because faster-whisper's PyAV decoder breaks across releases."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


def run(audio, model, device, lang, prompt):
    ct = "float16" if device == "cuda" else "int8"
    m = WhisperModel(model, device=device, compute_type=ct)
    segs, _ = m.transcribe(audio, language=lang, vad_filter=True, word_timestamps=True, initial_prompt=prompt or None, beam_size=5)
    return [{"s": round(w.start, 3), "e": round(w.end, 3), "w": w.word.strip()} for s in segs for w in s.words or []]


def sentences(words, max_len=8.0):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = words[i + 1]["s"] - w["e"] if i + 1 < len(words) else 9
        long_enough = cur[-1]["e"] - cur[0]["s"]
        if w["w"][-1:] in ".!?" or gap > .45 or long_enough > max_len or (w["w"][-1:] == "," and long_enough > 4):
            out.append({"t": cur[0]["s"], "end": cur[-1]["e"], "text": " ".join(x["w"] for x in cur)})
            cur = []
    return out


ap = argparse.ArgumentParser()
ap.add_argument("vo")
ap.add_argument("edit")
ap.add_argument("--model", default="large-v3")
ap.add_argument("--lang", default="vi")
ap.add_argument("--prompt", default="")
a = ap.parse_args()
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.vo, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
try:
    words = run(x, a.model, "cuda", a.lang, a.prompt)
except Exception as e:
    print("GPU unavailable, using CPU:", str(e)[:100])
    words = run(x, a.model, "cpu", a.lang, a.prompt)
edit = Path(a.edit)
edit.mkdir(parents=True, exist_ok=True)
sent = sentences(words)
(edit / "transcript.json").write_text(json.dumps({"duration": len(x) / 16000, "sentences": sent, "words": words}, ensure_ascii=False, indent=0), encoding="utf-8")
print(f"{len(words)} words, {len(sent)} sentences, {len(x) / 16000:.1f}s -> {edit / 'transcript.json'}")
