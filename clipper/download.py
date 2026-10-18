from pathlib import Path
import yt_dlp


def get_video(source: str, workdir: Path) -> Path:
    """Devuelve la ruta de un video local, o descarga el enlace con yt-dlp."""
    workdir.mkdir(parents=True, exist_ok=True)
    local = Path(source)
    if local.exists():
        return local

    opts = {
        "format": "bv*[height<=1080]+ba/b[height<=1080]",
        "merge_output_format": "mp4",
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "quiet": True,
        "noprogress": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(source, download=True)
        return Path(ydl.prepare_filename(info)).with_suffix(".mp4")
