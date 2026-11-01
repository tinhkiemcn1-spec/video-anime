"""Install the skill into Claude Code and the importer into DaVinci Resolve.

    python install.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = Path.home() / ".claude" / "skills" / "video-anime"
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True)
subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "make_sfx.py")], check=True)
if DEST.resolve() != ROOT:
    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(ROOT, DEST, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    print("Skill:", DEST)
subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts" / "resolve_build.py"), "install-script"], check=True)
if not shutil.which("ffmpeg"):
    print("Cần cài ffmpeg và thêm vào PATH.")
