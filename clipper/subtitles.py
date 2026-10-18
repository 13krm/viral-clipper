import textwrap
from pathlib import Path

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Sub,Arial,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,7,2,2,60,60,520,1
Style: Hook,Arial,72,&H00000000,&H00000000,&H0000E5FF,&H00000000,1,0,0,0,100,100,0,0,3,18,0,8,70,70,260,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

ACTIVE = r"{\c&H0000E5FF&\fscx112\fscy112}"   # amarillo y un poco más grande
NORMAL = r"{\c&H00FFFFFF&\fscx100\fscy100}"


def _t(sec: float) -> str:
    sec = max(sec, 0)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _clean(w: str) -> str:
    return w.replace("{", "").replace("}", "").replace("\\", "").upper()


def build_ass(segments: list[dict], clip_start: float, clip_end: float,
              hook: str | None, path: Path, words_per_line: int = 3) -> Path:
    words = [
        w for s in segments for w in s["words"]
        if w["start"] >= clip_start - 0.05 and w["end"] <= clip_end + 0.05
    ]
    lines = []

    if hook:
        wrapped = r"\N".join(textwrap.wrap(hook.upper(), 22))
        lines.append(f"Dialogue: 1,{_t(0)},{_t(3.2)},Hook,,0,0,0,,{wrapped}")

    for i in range(0, len(words), words_per_line):
        chunk = words[i:i + words_per_line]
        for j, w in enumerate(chunk):
            start = w["start"] - clip_start
            end = (chunk[j + 1]["start"] if j + 1 < len(chunk) else w["end"]) - clip_start
            text = " ".join(
                (ACTIVE if k == j else NORMAL) + _clean(x["word"]) for k, x in enumerate(chunk)
            )
            lines.append(f"Dialogue: 0,{_t(start)},{_t(max(end, start + 0.05))},Sub,,0,0,0,,{text}")

    path.write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8")
    return path
