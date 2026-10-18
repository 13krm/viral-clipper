# 🎬 Viral Clipper

Convierte videos largos en clips virales verticales (9:16) con subtítulos animados, hook y música. Gratis.

Usa faster-whisper (transcripción), Gemini (elige los momentos virales), OpenCV (encuadre) y ffmpeg (render).

## Publicar en Streamlit Community Cloud
1. Sube este proyecto a un repositorio de GitHub.
2. En https://share.streamlit.io → New app → elige el repositorio y `app.py`.
3. En *Advanced settings → Secrets* pega:
   ```
   GEMINI_API_KEY = "tu_clave"
   APP_PASSWORD = "una_contraseña"
   ```
4. Deploy. Usa el modelo de transcripción **tiny** o **base**.

## Música y efectos
Archivos libres de derechos en `assets/music/` y `assets/sfx/` (opcionales).

## Aviso
Usa solo videos propios o con permiso. Revisa los clips antes de publicar.
