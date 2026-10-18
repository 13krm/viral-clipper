import argparse
from dotenv import load_dotenv
from clipper.pipeline import run

load_dotenv()

ap = argparse.ArgumentParser(description="Generador de clips virales")
ap.add_argument("source", help="Ruta de un video o enlace")
ap.add_argument("--provider", choices=["gemini", "ollama"], default="gemini")
ap.add_argument("--model", default=None)
ap.add_argument("--whisper", default="small")
ap.add_argument("--lang", default=None)
ap.add_argument("--clips", type=int, default=5)
a = ap.parse_args()

for i, c in enumerate(run(a.source, a.provider, a.model, a.whisper, a.lang, a.clips), 1):
    print(f"#{i} score {c['score']} | {c['hook']}\n   {c['file']}")
