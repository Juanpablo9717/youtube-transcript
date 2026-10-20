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
        name = type(e).__name__
        why = "YouTube bloqueo la consulta (demasiadas seguidas)" if "Blocked" in name else name
        print(f"[captions] No disponibles: {why}; pruebo con el audio.", file=sys.stderr)
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


BLOQUEO = (
    "YouTube esta bloqueando las descargas desde tu conexion (pasa si haces muchas seguidas).\n"
    "  - Espera un rato (de minutos a una hora) y vuelve a intentar, o\n"
    "  - usa las cookies de tu navegador con sesion de YouTube abierta:\n"
    "      youtube-transcript URL --cookies-from-browser firefox   (tambien: chrome, edge, brave)\n"
    "    En Windows, Chrome/Edge deben estar cerrados; Firefox suele funcionar mejor."
)


def from_audio(url: str, model_size: str, lang: str | None, browser: str | None) -> str:
    ensure(("yt_dlp", "yt-dlp"), ("faster_whisper", "faster-whisper"), ("numpy", "numpy"))
    import yt_dlp
    from faster_whisper import WhisperModel

    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(tmp) / "audio.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
        print("[audio] Descargando audio...", file=sys.stderr)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            if "not a bot" in msg or "Sign in" in msg or "429" in msg:
                sys.exit(f"[audio] {BLOQUEO}")
            sys.exit(f"[audio] No pude descargar el audio: {msg.removeprefix('ERROR: ')}")
        except Exception as e:  # p.ej. no puede leer las cookies del navegador
            sys.exit(f"[audio] Error: {e}")
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


def write_stdout(text: str) -> None:
    """Imprime el texto. Si va por un pipe en Windows, usa la pagina de codigos de la
    consola para que PowerShell/cmd (| Set-Clipboard, | clip, ...) no rompan los acentos."""
    if sys.platform == "win32" and not sys.stdout.isatty():
        import ctypes

        cp = ctypes.windll.kernel32.GetConsoleOutputCP()
        if cp:
            sys.stdout.reconfigure(encoding=f"cp{cp}", errors="replace")
    else:
        sys.stdout.reconfigure(errors="replace")
    print(text)


def main():
    p = argparse.ArgumentParser(prog="youtube-transcript", description="Texto de un video de YouTube")
    p.add_argument("url")
    p.add_argument("--langs", nargs="+", default=["es", "en"], help="idiomas preferidos")
    p.add_argument("--whisper", action="store_true", help="forzar transcripcion por audio")
    p.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3")
    p.add_argument("-o", "--output", help="archivo de salida (por defecto <id>.txt); '-' = solo pantalla, sin archivo")
    p.add_argument("-p", "--print", action="store_true", help="ademas de guardar el archivo, muestra el texto en pantalla")
    p.add_argument("--cookies-from-browser", metavar="NAVEGADOR",
                   help="usa la sesion de YouTube de tu navegador si YouTube bloquea (firefox, chrome, edge, brave)")
    a = p.parse_args()

    vid = video_id(a.url)
    url = f"https://www.youtube.com/watch?v={vid}"

    text = None if a.whisper else from_captions(vid, a.langs)
    if not text:
        text = from_audio(url, a.model, None if len(a.langs) != 1 else a.langs[0], a.cookies_from_browser)

    words = len(text.split())
    if a.output == "-":
        write_stdout(text)
        print(f"Listo ({words} palabras)", file=sys.stderr)
        return

    out = Path(a.output or f"{vid}.txt")
    out.write_text(text, encoding="utf-8")
    if a.print:
        write_stdout(text)
    print(f"Listo: {out} ({words} palabras)", file=sys.stderr)


if __name__ == "__main__":
    main()
