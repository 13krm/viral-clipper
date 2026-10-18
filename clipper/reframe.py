from pathlib import Path
import cv2


def video_size(video: Path) -> tuple[int, int]:
    cap = cv2.VideoCapture(str(video))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h


def face_center_x(video: Path, start: float, end: float, step: float = 1.0) -> float | None:
    """Posición horizontal media (0-1) de la cara más grande durante el clip."""
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(str(video))
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    xs = []
    t = start
    while t < end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, None, fx=0.4, fy=0.4)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.2, 5, minSize=(40, 40))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            xs.append((x + w / 2) / small.shape[1])
        t += step
    cap.release()
    if not xs:
        return None
    xs.sort()
    return xs[len(xs) // 2]  # mediana: ignora falsos positivos


def crop_filter(video: Path, start: float, end: float) -> str:
    """Filtro ffmpeg que recorta a 9:16 centrado en la cara (o en el centro)."""
    w, h = video_size(video)
    cw = int(h * 9 / 16) // 2 * 2
    if cw >= w:  # el video ya es vertical o casi
        return "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    cx = face_center_x(video, start, end)
    cx = 0.5 if cx is None else cx
    x = int(min(max(cx * w - cw / 2, 0), w - cw)) // 2 * 2
    return f"crop={cw}:{h}:{x}:0,scale=1080:1920"
