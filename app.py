import os
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from clipper.pipeline import run

load_dotenv()
st.set_page_config(page_title="Viral Clipper", page_icon="🎬", layout="wide")

CSS = """
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: radial-gradient(1200px 600px at 10% -10%, #2a1458 0%, transparent 60%),
        radial-gradient(900px 500px at 100% 0%, #4a123f 0%, transparent 55%), #0B0B12;}
.block-container {max-width: 1100px; padding-top: 2.5rem;}
.hero {text-align:center; margin: 1rem 0 2rem;}
.hero h1 {font-size: 3.2rem; font-weight: 800; margin: 0; letter-spacing:-1px;
          background: linear-gradient(90deg,#A78BFA,#F472B6,#FB923C); -webkit-background-clip:text;
          -webkit-text-fill-color: transparent;}
.hero p {color:#A1A1B5; font-size:1.1rem; margin-top:.4rem;}
.card {background: rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
       border-radius: 18px; padding: 1.2rem 1.3rem; margin-bottom: 1rem; backdrop-filter: blur(6px);}
.badge {display:inline-block; padding:.2rem .7rem; border-radius:999px; font-weight:700; font-size:.85rem;
        background: linear-gradient(90deg,#8B5CF6,#EC4899); color:white;}
.hook {font-weight:700; font-size:1.05rem; margin:.6rem 0 .2rem;}
.muted {color:#A1A1B5; font-size:.88rem;}
.steps {display:flex; gap:.6rem; flex-wrap:wrap; margin:.3rem 0 .8rem;}
.step {padding:.3rem .8rem; border-radius:999px; font-size:.85rem; border:1px solid rgba(255,255,255,.12); color:#A1A1B5;}
.step.on {background: rgba(139,92,246,.25); color:#fff; border-color:#8B5CF6;}
.step.done {background: rgba(16,185,129,.18); color:#6EE7B7; border-color: rgba(16,185,129,.5);}
div.stButton > button, div.stDownloadButton > button {
    border-radius: 12px; border: 0; font-weight: 700; padding:.65rem 1.4rem;}
div.stButton > button[kind="primary"] {background: linear-gradient(90deg,#8B5CF6,#EC4899); color:white;}
[data-testid="stFileUploader"] section {border-radius:16px; border:2px dashed rgba(167,139,250,.5);
    background: rgba(139,92,246,.06);}
.stProgress > div > div > div > div {background: linear-gradient(90deg,#8B5CF6,#EC4899);}
video {border-radius: 14px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><h1>🎬 Viral Clipper</h1>'
    '<p>Sube un video largo y la IA crea clips virales verticales con subtítulos, hook y música.</p></div>',
    unsafe_allow_html=True,
)

# ---------- contraseña opcional (para que nadie gaste tu clave de Gemini) ----------
# En Streamlit Cloud los secretos viven en st.secrets: los copiamos al entorno
for _k in ("GEMINI_API_KEY", "APP_PASSWORD"):
    try:
        if _k in st.secrets:
            os.environ.setdefault(_k, str(st.secrets[_k]))
    except Exception:
        pass

PASSWORD = os.environ.get("APP_PASSWORD")
if PASSWORD and not st.session_state.get("auth"):
    pw = st.text_input("Contraseña", type="password")
    if pw:
        if pw == PASSWORD:
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

if not os.environ.get("GEMINI_API_KEY"):
    st.error("Falta la clave GEMINI_API_KEY (en Hugging Face: Settings → Variables and secrets).")
    st.stop()


# ---------- trabajos en segundo plano (siguen aunque cierres la pestaña) ----------
@st.cache_resource
def jobs() -> dict:
    return {}


def running() -> bool:
    return any(j["clips"] is None and j["error"] is None for j in jobs().values())


def start_job(source, whisper, lang, n):
    jid = uuid.uuid4().hex[:8]
    J = jobs()
    J[jid] = {"pct": 0.02, "msg": "Empezando...", "clips": None, "error": None, "t0": time.time()}

    def work():
        try:
            def cb(msg, frac):
                J[jid].update(msg=msg, pct=frac)
            J[jid]["clips"] = run(source, "gemini", None, whisper, lang, n, progress=cb)
        except Exception as e:
            J[jid]["error"] = str(e)

    threading.Thread(target=work, daemon=True).start()
    return jid


def steps_html(pct: float) -> str:
    names = [("Video", 0.15), ("Transcripción", 0.5), ("Análisis IA", 0.55), ("Render", 1.0)]
    out, prev = [], 0.0
    for name, upto in names:
        cls = "done" if pct >= upto else ("on" if pct >= prev else "")
        out.append(f'<span class="step {cls}">{name}</span>')
        prev = upto
    return f'<div class="steps">{"".join(out)}</div>'


jid = st.query_params.get("job")
J = jobs()

# ---------- vista: trabajo en curso / resultados ----------
if jid and jid in J:
    job = J[jid]
    if job["error"]:
        msg = job["error"]
        if "429" in msg or "quota" in msg.lower():
            msg = "Se alcanzó el límite gratuito de Gemini. Espera unos minutos e inténtalo de nuevo."
        st.error(f"Algo falló: {msg}")
        if st.button("Volver"):
            st.query_params.clear()
            st.rerun()
        st.stop()

    if job["clips"] is None:
        el = int(time.time() - job["t0"])
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(steps_html(job["pct"]), unsafe_allow_html=True)
        st.progress(min(job["pct"], 1.0))
        st.write(f"**{job['msg']}**  ·  {el // 60} min {el % 60:02d} s")
        st.caption("Puedes cerrar esta pestaña: el trabajo sigue. Guarda este enlace para volver.")
        st.markdown("</div>", unsafe_allow_html=True)
        time.sleep(3)
        st.rerun()

    clips = job["clips"]
    st.markdown(f"### ✨ {len(clips)} clips listos")
    zip_path = shutil.make_archive(f"workdir/clips_{jid}", "zip", Path(clips[0]["file"]).parent)
    with open(zip_path, "rb") as f:
        st.download_button("⬇️ Descargar todos (ZIP)", f, file_name="clips.zip", type="primary")

    cols = st.columns(3)
    for i, c in enumerate(clips):
        with cols[i % 3]:
            st.markdown(
                f'<div class="card"><span class="badge">🔥 {c["score"]}/100</span>'
                f'<div class="hook">“{c["hook"]}”</div><div class="muted">{c["title"]}</div></div>',
                unsafe_allow_html=True,
            )
            st.video(c["file"])
            st.caption(c["reason"])
            with open(c["file"], "rb") as f:
                st.download_button("Descargar", f, file_name=Path(c["file"]).name, key=f"d{i}")
    st.divider()
    if st.button("➕ Nuevo video"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# ---------- vista: formulario ----------
if running():
    st.info("Hay un video procesándose ahora mismo. Espera a que termine.")
    st.stop()

st.markdown('<div class="card">', unsafe_allow_html=True)
upload = st.file_uploader("Arrastra aquí tu video", type=["mp4", "mov", "mkv", "webm"])
url = st.text_input("…o pega un enlace (puede fallar en servidores públicos; si falla, sube el archivo)")
with st.expander("⚙️ Ajustes"):
    c1, c2, c3 = st.columns(3)
    whisper = c1.selectbox("Precisión de transcripción", ["tiny", "base", "small"], index=1,
                           help="Más precisa = más lenta")
    lang = c2.text_input("Idioma (es, en...)", "es") or None
    n = c3.slider("Número de clips", 1, 10, 5)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("🚀 Generar clips", type="primary"):
    source = url.strip()
    if upload:
        up_dir = Path("workdir/uploads")
        up_dir.mkdir(parents=True, exist_ok=True)
        dest = up_dir / f"{uuid.uuid4().hex[:6]}_{Path(upload.name).name}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(upload, f)
        source = str(dest)
    if not source:
        st.warning("Sube un video o pega un enlace.")
    else:
        st.query_params["job"] = start_job(source, whisper, lang, n)
        st.rerun()
