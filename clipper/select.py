import json
import os
import re
import requests

PROMPT = """Eres un editor experto en contenido viral para TikTok, Reels y YouTube Shorts.
Te paso la transcripción de un video con marcas de tiempo en segundos: [inicio] texto.

Elige los {n} fragmentos con MÁS potencial viral. Reglas:
- Cada fragmento dura entre {min_d} y {max_d} segundos.
- Debe entenderse solo, sin contexto previo, y empezar con una frase que enganche.
- Prioriza: opiniones polémicas, historias con giro, datos sorprendentes, emoción fuerte, consejos accionables, frases citables.
- Los fragmentos no se pueden solapar.
- Usa los tiempos exactos de la transcripción.
- "hook": frase corta (máx. 10 palabras) para mostrar en pantalla los primeros segundos, en el idioma del video.
- "title": título para publicar el clip.
- "score": de 1 a 100.

Devuelve SOLO un JSON con esta forma:
{{"clips": [{{"start": 0.0, "end": 0.0, "score": 0, "title": "", "hook": "", "reason": ""}}]}}

TRANSCRIPCIÓN:
{transcript}
"""


def _format_transcript(segments: list[dict]) -> str:
    return "\n".join(f"[{s['start']:.1f}] {s['text']}" for s in segments)


def _call_gemini(prompt: str, model: str) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_mime_type": "application/json", "temperature": 0.4},
    )
    return resp.text


def _call_ollama(prompt: str, model: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
            "options": {"num_ctx": 16384, "temperature": 0.4},
        },
        timeout=900,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def _snap(clip: dict, segments: list[dict]) -> dict:
    """Ajusta inicio/fin a los límites de frases para no cortar a mitad de palabra."""
    start = min(segments, key=lambda s: abs(s["start"] - clip["start"]))["start"]
    end = min(segments, key=lambda s: abs(s["end"] - clip["end"]))["end"]
    return {**clip, "start": start, "end": end}


def select_clips(
    segments: list[dict],
    provider: str = "gemini",
    model: str | None = None,
    n: int = 5,
    min_d: int = 25,
    max_d: int = 60,
) -> list[dict]:
    prompt = PROMPT.format(n=n, min_d=min_d, max_d=max_d, transcript=_format_transcript(segments))

    if provider == "gemini":
        raw = _call_gemini(prompt, model or "gemini-2.5-flash")
    else:
        raw = _call_ollama(prompt, model or "qwen2.5:14b")

    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    clips = json.loads(raw)["clips"]

    valid = []
    for c in clips:
        c = _snap(c, segments)
        dur = c["end"] - c["start"]
        if min_d - 5 <= dur <= max_d + 15:
            valid.append(c)

    # quita solapes quedándose con el de mayor puntuación
    valid.sort(key=lambda c: c.get("score", 0), reverse=True)
    final = []
    for c in valid:
        if all(c["end"] <= f["start"] or c["start"] >= f["end"] for f in final):
            final.append(c)
    return final[:n]
