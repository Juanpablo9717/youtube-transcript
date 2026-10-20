# yt-texto

Saca el texto de un video de YouTube con un solo comando.

1. Si el video tiene subtítulos (manuales o automáticos), los usa. Tarda segundos.
2. Si no tiene, descarga solo el audio y lo transcribe **en tu PC** con [Whisper](https://github.com/SYSTRAN/faster-whisper). Es gratis, no usa APIs y no necesita ffmpeg.

## Instalación

El instalador revisa qué falta y lo instala: Python (si no lo tienes), un entorno aislado en `~/.yt-texto` y el comando `yt-texto` en tu PATH.

**Windows** (PowerShell):
```powershell
irm https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.ps1 | iex
```

**macOS / Linux**:
```bash
curl -fsSL https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.sh | sh
```

Si clonaste el repo, también puedes correr `install.ps1` o `sh install.sh` desde la carpeta.

| Sistema | Si falta Python lo instala con |
|---|---|
| Windows | `winget` |
| macOS | `brew` |
| Debian / Ubuntu | `apt` (incluye `python3-venv`) |
| Fedora / RHEL | `dnf` |
| Arch | `pacman` |
| openSUSE | `zypper` |
| Alpine | `apk` |

Para instalar sin Whisper (más liviano, solo subtítulos): `install.ps1 -SinAudio` o `sh install.sh --sin-audio`. Si después hace falta, `yt-texto` instala Whisper solo la primera vez que lo necesite.

## Uso

```bash
yt-texto "https://www.youtube.com/watch?v=OgHQTezKE4Q"
```

Deja `OgHQTezKE4Q.txt` en la carpeta actual.

| Opción | Qué hace |
|---|---|
| `--langs es en` | Idiomas preferidos para los subtítulos (por defecto `es en`) |
| `--whisper` | Ignora los subtítulos y transcribe el audio |
| `--model small` | Modelo de Whisper: `tiny`, `base`, `small`, `medium`, `large-v3`. Más grande = más preciso y más lento |
| `-o archivo.txt` | Nombre del archivo de salida |

Como referencia, un video de 9 minutos con `--model base` tarda alrededor de 1 minuto en CPU. La primera vez se descarga el modelo.

## Desinstalar

- Windows: borra `%USERPROFILE%\.yt-texto` y quita `%USERPROFILE%\.yt-texto\bin` de tu PATH de usuario.
- macOS / Linux: `rm -rf ~/.yt-texto ~/.local/bin/yt-texto`
