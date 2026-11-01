"""manifest.json -> FCPXML timeline -> DaVinci Resolve (Free and Studio).

    python -X utf8 resolve_build.py <edit> [--name "Tên timeline"] [--push] [--check]
    python -X utf8 resolve_build.py install-script

Tracks: V1 base, V2 characters (alpha), V3 text, V4 meme clips (opacity), A1 VO, A2 SFX, A3 music.
Without --push, or if external scripting is refused (Resolve Free), open the timeline with
Workspace > Scripts > video anime Import. An existing timeline is never replaced.
--check renders the timeline from Resolve (540p) and compares it with preview.mp4, which proves
the layers, the alpha and the media links really work; it needs Studio.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import quoteattr

FPS = 30
POINTER = Path(os.environ.get("APPDATA", Path.home())) / "video-anime" / "last_timeline.json"


def F(sec):
    return round(sec * FPS)


def T(frames):
    v = Fraction(frames, FPS)
    return f"{v.numerator}s" if v.denominator == 1 else f"{v.numerator}/{v.denominator}s"


def url(p):
    return "file:///" + quote(Path(p).resolve().as_posix().lstrip("/"), safe="/:")


def probe(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,sample_rate,channels:format=duration", "-of", "json", str(p)],
                       capture_output=True, text=True, encoding="utf-8")
    d = json.loads(o.stdout or "{}")
    return {"dur": float(d.get("format", {}).get("duration") or 0),
            "v": next((s for s in d.get("streams", []) if s["codec_type"] == "video"), None),
            "a": next((s for s in d.get("streams", []) if s["codec_type"] == "audio"), None)}


def build(edit, name):
    m = json.loads((edit / "manifest.json").read_text(encoding="utf-8"))
    res = [f'<format id="r1" frameDuration="1/{FPS}s" width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>',
           '<format id="r2" name="FFVideoFormatRateUndefined" width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>']
    assets, nid = {}, [2]

    def asset(path, kind):
        if path in assets:
            return assets[path]
        nid[0] += 1
        aid = f"r{nid[0]}"
        info = probe(path)
        stem = Path(path).stem
        a = [f'id="{aid}"', f"name={quoteattr(stem)}", 'start="0s"']
        if kind == "still":
            a += ['duration="0s"', 'hasVideo="1"', 'format="r2"']
        else:
            a.append(f'duration="{T(F(info["dur"]))}"')
            if info["v"] and kind == "video":
                a += ['hasVideo="1"', 'format="r1"']
            if info["a"]:
                a += ['hasAudio="1"', 'audioSources="1"', f'audioChannels="{info["a"].get("channels", 2)}"', f'audioRate="{info["a"].get("sample_rate", 48000)}"']
        res.append(f"<asset {' '.join(a)}><media-rep kind=\"original-media\" src={quoteattr(url(path))}/></asset>")
        assets[path] = aid
        return aid

    clips = m["clips"]
    bases = sorted((c for c in clips if c["track"] == 1), key=lambda c: c["t"])
    spine = []
    for i, b in enumerate(bases):
        off = F(b["t"])
        dur = F(bases[i + 1]["t"]) - off if i + 1 < len(bases) else F(b["end"]) - off
        spine.append({"b": b, "off": off, "dur": dur, "kids": []})

    def parent_of(frame):
        return max((s for s in spine if s["off"] <= frame), key=lambda s: s["off"], default=spine[0])

    def attach(c, lane, audio_only=False):
        off = F(c["t"])
        p = parent_of(off)
        aid = asset(c["file"], "audio" if audio_only else c["kind"])
        local = off - p["off"]
        dur = (F(c["end"]) - off) if c.get("end") else F(probe(c["file"])["dur"])
        inner = ""
        if c.get("opacity") is not None:
            inner += f'<adjust-blend amount="{c["opacity"]:.3f}"/>'
        if c.get("gain") is not None:
            inner += f'<adjust-volume amount="{c["gain"]}dB"/>'
        if c["kind"] == "still":
            p["kids"].append(f'<video ref="{aid}" lane="{lane}" name={quoteattr(Path(c["file"]).stem)} offset="{T(local)}" start="0s" duration="{T(dur)}">{inner}</video>')
        else:
            p["kids"].append(f'<asset-clip ref="{aid}" lane="{lane}" name={quoteattr(Path(c["file"]).stem)} offset="{T(local)}" start="{T(F(c.get("src", 0)))}" '
                             f'duration="{T(dur)}" tcFormat="NDF"{" srcEnable=\"audio\"" if audio_only else ""}>{inner}</asset-clip>')

    for c in clips:
        if c["track"] in (2, 3, 4):
            attach(c, c["track"] - 1)
        elif c["track"] == -2:
            attach(c, -2, True)  # Resolve numbers audio from the lowest lane: -3 = A1
    total = spine[-1]["off"] + spine[-1]["dur"]
    attach({"file": m["vo"], "t": 0, "end": total / FPS, "kind": "audio"}, -3, True)
    if m.get("music"):
        attach({"file": m["music"], "t": 0, "end": total / FPS, "kind": "audio", "gain": m.get("music_db", -24)}, -1, True)
    body = []
    for s in spine:
        b = s["b"]
        aid = asset(b["file"], b["kind"])
        nm = quoteattr(Path(b["file"]).stem)
        if b["kind"] == "still":
            body.append(f'<video ref="{aid}" name={nm} offset="{T(s["off"])}" start="0s" duration="{T(s["dur"])}">{"".join(s["kids"])}</video>')
        else:
            body.append(f'<asset-clip ref="{aid}" name={nm} offset="{T(s["off"])}" start="0s" duration="{T(s["dur"])}" tcFormat="NDF">{"".join(s["kids"])}</asset-clip>')
    nl = "\n"
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="1.10">\n'
           f'<resources>\n{nl.join(res)}\n</resources>\n<library><event name={quoteattr(name)}><project name={quoteattr(name)}>'
           f'<sequence format="r1" duration="{T(total)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k"><spine>\n'
           f'{nl.join(body)}\n</spine></sequence></project></event></library>\n</fcpxml>\n')
    out = edit / "resolve"
    out.mkdir(exist_ok=True)
    fx = out / "timeline.fcpxml"
    fx.write_text(xml, encoding="utf-8")
    POINTER.parent.mkdir(parents=True, exist_ok=True)
    POINTER.write_text(json.dumps({"fcpxml": str(fx), "name": name, "fps": FPS, "width": 1920, "height": 1080}, ensure_ascii=False), encoding="utf-8")
    print(f"FCPXML: {fx}\n  {len(spine)} shots, {len(clips)} layers, {total / FPS:.2f}s")
    return fx


def connect():
    if sys.platform == "win32":
        api = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting"
        os.environ.setdefault("RESOLVE_SCRIPT_API", str(api))
        os.environ.setdefault("RESOLVE_SCRIPT_LIB", str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blackmagic Design/DaVinci Resolve/fusionscript.dll"))
        sys.path.append(str(api / "Modules"))
    import DaVinciResolveScript as dvr
    return dvr.scriptapp("Resolve")


def timeline_names(p):
    return {p.GetTimelineByIndex(i).GetName() for i in range(1, p.GetTimelineCount() + 1)}


def push(fx, name):
    r = connect()
    if r is None:
        sys.exit("Không kết nối được Resolve qua script ngoài (bản Free hoặc External scripting chưa bật). "
                 "Dùng Workspace > Scripts > video anime Import.")
    pm = r.GetProjectManager()
    p = pm.GetCurrentProject()
    if name in timeline_names(p):
        sys.exit(f"Timeline '{name}' đã có, chọn tên khác (không ghi đè).")
    pool = p.GetMediaPool()
    if not pool.GetRootFolder().GetClipList():
        p.SetSetting("timelineFrameRate", str(FPS))
        p.SetSetting("timelineResolutionWidth", "1920")
        p.SetSetting("timelineResolutionHeight", "1080")
    tl = pool.ImportTimelineFromFile(str(fx), {"timelineName": name, "importSourceClips": True})
    if not tl:
        sys.exit("Resolve từ chối file: mở bằng File > Import > Timeline để xem lỗi.")
    p.SetCurrentTimeline(tl)
    r.OpenPage("edit")
    print(f"Timeline '{tl.GetName()}' trong project '{p.GetName()}': V{tl.GetTrackCount('video')} A{tl.GetTrackCount('audio')}, {tl.GetEndFrame() - tl.GetStartFrame()} frames")


def check(edit, name):
    import time
    r = connect()
    p = r.GetProjectManager().GetCurrentProject()
    tl = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == name)
    p.SetCurrentTimeline(tl)
    p.SetCurrentRenderFormatAndCodec("mp4", "H264")
    out = edit / "resolve"
    p.SetRenderSettings({"TargetDir": str(out), "CustomName": "check", "SelectAllFrames": True, "ExportVideo": True, "ExportAudio": True,
                         "FormatWidth": 960, "FormatHeight": 540})
    job = p.AddRenderJob()
    p.StartRendering(job)
    while p.IsRenderingInProgress():
        time.sleep(1)
    st = p.GetRenderJobStatus(job)
    p.DeleteRenderJob(job)
    print("render:", st)
    rendered, pv = out / "check.mp4", edit / "preview.mp4"
    d = probe(rendered)["dur"]
    print(f"check.mp4 {d:.2f}s, preview {probe(pv)['dur']:.2f}s")
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(rendered), "-i", str(pv), "-lavfi", "[0:v]fps=2,format=gray[a];[1:v]fps=2,format=gray[b];[a][b]psnr", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    print(next((l for l in o.splitlines() if "PSNR" in l), "psnr n/a"))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(rendered), "-vf", f"fps={min(1.0, 16 / max(d, 1)):.4f},scale=480:-1,tile=4x4", "-frames:v", "1", str(out / "check_sheet.jpg")], check=True)
    print("xem:", out / "check_sheet.jpg")


MENU_SCRIPT = r'''"""video anime: import the latest timeline. Workspace > Scripts > video anime Import."""
import json, os
try:
    resolve
except NameError:
    import DaVinciResolveScript as dvr
    resolve = dvr.scriptapp("Resolve")
info = json.load(open(os.path.join(os.environ.get("APPDATA", ""), "video-anime", "last_timeline.json"), encoding="utf-8"))
project = resolve.GetProjectManager().GetCurrentProject()
pool = project.GetMediaPool()
if not pool.GetRootFolder().GetClipList():
    project.SetSetting("timelineFrameRate", str(info["fps"]))
    project.SetSetting("timelineResolutionWidth", str(info["width"]))
    project.SetSetting("timelineResolutionHeight", str(info["height"]))
tl = pool.ImportTimelineFromFile(info["fcpxml"], {"timelineName": info["name"], "importSourceClips": True})
print("video anime:", tl.GetName() if tl else "import FAILED, try File > Import > Timeline")
if tl:
    project.SetCurrentTimeline(tl)
    resolve.OpenPage("edit")
'''


def install_script():
    if sys.platform == "win32":
        d = Path(os.environ["APPDATA"]) / "Blackmagic Design/DaVinci Resolve/Support/Fusion/Scripts/Utility"
    elif sys.platform == "darwin":
        d = Path.home() / "Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility"
    else:
        d = Path.home() / ".local/share/DaVinciResolve/Fusion/Scripts/Utility"
    d.mkdir(parents=True, exist_ok=True)
    (d / "video anime Import.py").write_text(MENU_SCRIPT, encoding="utf-8")
    print("Đã cài:", d / "video anime Import.py")


if __name__ == "__main__":
    if sys.argv[1:] == ["install-script"]:
        install_script()
        sys.exit()
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("--name")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    edit = Path(a.edit).resolve()
    name = a.name or edit.name
    fx = build(edit, name)
    if a.push:
        push(fx, name)
    if a.check:
        check(edit, name)
