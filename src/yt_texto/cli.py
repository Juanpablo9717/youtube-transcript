"""Saca el texto de un video de YouTube.

1. Intenta con los subtitulos de YouTube (manuales o automaticos).
2. Si no hay, descarga solo el audio y lo transcribe localmente con Whisper.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

from .deps import ensure


def video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([\w-]{11})", url)
    if m:
        return m.group(1)
    if re.fullmatch(r"[\w-]{11}", url):
        return url
    sys.exit(f"No pude sacar el ID del video de: {url}")


def from_captions(vid: str, langs: list[str]) -> str | None:
    ensure(("youtube_transcript_api", "youtube-transcript-api"))
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    try:
        tlist = api.list(vid)
    except Exception as e:
        print(f"[captions] No disponibles: {type(e).__name__}", file=sys.stderr)
        return None
    try:
        t = tlist.find_transcript(langs)
    except Exception:
        # Cualquier idioma disponible, traducido al primero pedido si se puede
        t = next(iter(tlist), None)
        if t is None:
            return None
        if t.is_translatable and t.language_code not in langs:
            try:
                t = t.translate(langs[0])
            except Exception:
                pass
    kind = "auto" if t.is_generated else "manual"
    print(f"[captions] {t.language_code} ({kind})", file=sys.stderr)
    snippets = t.fetch()
    return " ".join(s.text.replace("\n", " ") for s in snippets if s.text.strip())


def load_audio(path: Path):
    """Decodifica a 16 kHz mono float32 (lo que espera Whisper) sin necesitar ffmpeg."""
    import av
    import numpy as np

    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    chunks = []
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            for f in resampler.resample(frame):
                chunks.append(f.to_ndarray().reshape(-1))
        for f in resampler.resample(None):
            chunks.append(f.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def from_audio(url: str, model_size: str, lang: str | None) -> str:
    ensure(("yt_dlp", "yt-dlp"), ("faster_whisper", "faster-whisper"), ("numpy", "numpy"))
    import yt_dlp
    from faster_whisper import WhisperModel

    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(tmp) / "audio.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        print("[audio] Descargando audio...", file=sys.stderr)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        audio = next(Path(tmp).glob("audio.*"))

        print(f"[audio] Transcribiendo con Whisper '{model_size}' (CPU)...", file=sys.stderr)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(load_audio(audio), language=lang, vad_filter=True)
        print(f"[audio] Idioma detectado: {info.language}", file=sys.stderr)
        parts = []
        for seg in segments:
            parts.append(seg.text.strip())
            print(f"  {seg.end / 60:5.1f} min", end="\r", file=sys.stderr)
        print(file=sys.stderr)
        return " ".join(parts)


def main():
    p = argparse.ArgumentParser(prog="yt-texto", description="Texto de un video de YouTube")
    p.add_argument("url")
    p.add_argument("--langs", nargs="+", default=["es", "en"], help="idiomas preferidos")
    p.add_argument("--whisper", action="store_true", help="forzar transcripcion por audio")
    p.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3")
    p.add_argument("-o", "--output", help="archivo de salida (por defecto <id>.txt)")
    a = p.parse_args()

    vid = video_id(a.url)
    url = f"https://www.youtube.com/watch?v={vid}"

    text = None if a.whisper else from_captions(vid, a.langs)
    if not text:
        text = from_audio(url, a.model, None if len(a.langs) != 1 else a.langs[0])

    out = Path(a.output or f"{vid}.txt")
    out.write_text(text, encoding="utf-8")
    print(f"Listo: {out} ({len(text.split())} palabras)", file=sys.stderr)


if __name__ == "__main__":
    main()
