import json
from pathlib import Path
from faster_whisper import WhisperModel


def transcribe(video: Path, workdir: Path, model_size: str = "small", language: str | None = None) -> list[dict]:
    """Transcribe con marcas de tiempo por palabra. Cachea el resultado en JSON."""
    cache = workdir / f"{video.stem}.transcript.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(video), word_timestamps=True, vad_filter=True, language=language
    )
    print(f"Idioma detectado: {info.language}")

    result = []
    for seg in segments:
        result.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": [
                {"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)}
                for w in (seg.words or [])
            ],
        })
    cache.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
