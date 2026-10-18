import random
import re
import subprocess
from pathlib import Path

from .reframe import crop_filter
from .subtitles import build_ass

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg"}


def _pick(folder: Path) -> Path | None:
    files = [f for f in folder.glob("*") if f.suffix.lower() in AUDIO_EXT] if folder.exists() else []
    return random.choice(files) if files else None


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_")[:40] or "clip"


def render_clip(video: Path, segments: list[dict], clip: dict, index: int, out_dir: Path,
                assets: Path = Path("assets"), music_volume: float = 0.07) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    start, end = clip["start"], clip["end"]
    dur = end - start
    name = f"clip{index:02d}_{_slug(clip.get('title', ''))}"
    ass_name = f"{name}.ass"
    build_ass(segments, start, end, clip.get("hook"), out_dir / ass_name)

    vf = crop_filter(video, start, end) + f",ass={ass_name}"
    music = _pick(assets / "music")
    whoosh = _pick(assets / "sfx")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}", "-t", f"{dur}", "-i", str(video.resolve())]
    inputs = 1
    mix = ["[0:a]volume=1.0[v]"]
    labels = ["[v]"]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music.resolve())]
        mix.append(f"[{inputs}:a]volume={music_volume},afade=t=in:d=1,afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5[m]")
        labels.append("[m]")
        inputs += 1
    if whoosh:
        cmd += ["-i", str(whoosh.resolve())]
        mix.append(f"[{inputs}:a]volume=0.5[w]")
        labels.append("[w]")
        inputs += 1
    mix.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0[a]")

    out_file = f"{name}.mp4"
    cmd += [
        "-filter_complex", f"[0:v]{vf}[vid];" + ";".join(mix),
        "-map", "[vid]", "-map", "[a]", "-t", f"{dur}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_file,
    ]
    # cwd = carpeta de salida: evita problemas de rutas de Windows con el filtro ass
    subprocess.run(cmd, check=True, cwd=out_dir)
    (out_dir / ass_name).unlink(missing_ok=True)
    return out_dir / out_file
