import json
from pathlib import Path
from typing import Callable

from .download import get_video
from .transcribe import transcribe
from .select import select_clips
from .render import render_clip


def run(source: str, provider="gemini", model=None, whisper="small", lang=None,
        n_clips=5, progress: Callable[[str, float], None] | None = None) -> list[dict]:
    p = progress or (lambda msg, frac: print(msg))
    workdir, out_dir = Path("workdir"), Path("output")

    p("Obteniendo video...", 0.05)
    video = get_video(source, workdir)

    p("Transcribiendo (puede tardar unos minutos)...", 0.15)
    segments = transcribe(video, workdir, whisper, lang)

    p("La IA está eligiendo los mejores momentos...", 0.5)
    clips = select_clips(segments, provider, model, n_clips)
    (workdir / f"{video.stem}.clips.json").write_text(
        json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8")

    results = []
    for i, c in enumerate(clips, 1):
        p(f"Renderizando clip {i}/{len(clips)}...", 0.55 + 0.45 * (i - 1) / max(len(clips), 1))
        c["file"] = str(render_clip(video, segments, c, i, out_dir / video.stem))
        results.append(c)
    p("¡Listo!", 1.0)
    return results
