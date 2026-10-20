# youtube-transcript

Saca el texto de cualquier video de YouTube con un solo comando.

- Si el video tiene subtítulos (manuales o automáticos), los usa. Tarda segundos.
- Si no tiene, descarga solo el audio y lo transcribe **en tu PC** con [Whisper](https://github.com/SYSTRAN/faster-whisper). Es gratis, no usa APIs ni cuentas, y no necesita ffmpeg.

```text
$ youtube-transcript "https://www.youtube.com/watch?v=OgHQTezKE4Q"
[captions] es (auto)
Listo: OgHQTezKE4Q.txt (1696 palabras)
```

## Instalación

Un solo comando. El instalador revisa qué te falta y lo instala solo: Python (si no lo tienes), un entorno aislado en `~/.youtube-transcript` (no toca tu Python) y el comando `youtube-transcript` en tu PATH.

**Windows** (PowerShell):
```powershell
irm https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.ps1 | iex
```

**macOS / Linux**:
```bash
curl -fsSL https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.sh | sh
```

Cuando termine, **abre una terminal nueva** para que reconozca el comando.

<details>
<summary>Qué usa para instalar Python en cada sistema</summary>

| Sistema | Gestor |
|---|---|
| Windows | `winget` |
| macOS | `brew` |
| Debian / Ubuntu | `apt` (incluye `python3-venv`) |
| Fedora / RHEL | `dnf` |
| Arch | `pacman` |
| openSUSE | `zypper` |
| Alpine | `apk` |

</details>

<details>
<summary>Otras formas de instalar</summary>

- **Desde una copia del repo:**
  ```bash
  git clone https://github.com/Juanpablo9717/youtube-transcript
  cd youtube-transcript
  sh install.sh                                          # macOS / Linux
  powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
  ```
- **Sin Whisper** (más liviano, solo subtítulos): `install.ps1 -SinAudio` o `sh install.sh --sin-audio`. Si después un video lo necesita, Whisper se instala solo la primera vez.
- **Con pip, si ya manejas tus entornos:**
  ```bash
  pip install "youtube-transcript[audio] @ https://github.com/Juanpablo9717/youtube-transcript/archive/refs/heads/main.zip"
  ```

</details>

## Cómo usar

### Lo básico

```bash
youtube-transcript "https://www.youtube.com/watch?v=OgHQTezKE4Q"
```

Crea `OgHQTezKE4Q.txt` en la carpeta donde estás, con todo el texto del video en un solo bloque. En pantalla solo ves el progreso; para ver también el texto agrega `--print`. Acepta cualquier formato de link (`youtu.be/...`, `/shorts/...`, `/live/...`) o solo el ID (`OgHQTezKE4Q`).

### Ejemplos

```bash
# Ver el texto en pantalla (y guardarlo igual)
youtube-transcript OgHQTezKE4Q --print

# Solo en pantalla, sin crear archivo
youtube-transcript OgHQTezKE4Q -o -

# Copiarlo directo al portapapeles
youtube-transcript OgHQTezKE4Q -o - | Set-Clipboard   # Windows (PowerShell)
youtube-transcript OgHQTezKE4Q -o - | pbcopy          # macOS
youtube-transcript OgHQTezKE4Q -o - | xclip -sel c    # Linux

# Guardar con otro nombre
youtube-transcript "https://youtu.be/OgHQTezKE4Q" -o claude-design.txt

# Preferir subtítulos en inglés
youtube-transcript OgHQTezKE4Q --langs en

# Video sin subtítulos (o con subtítulos malos): transcribir el audio
youtube-transcript OgHQTezKE4Q --whisper

# Más precisión (más lento) o más velocidad (menos preciso)
youtube-transcript OgHQTezKE4Q --whisper --model medium
youtube-transcript OgHQTezKE4Q --whisper --model tiny

# Si YouTube te bloquea, usar tu sesión del navegador
youtube-transcript OgHQTezKE4Q --cookies-from-browser firefox
```

### Opciones

| Opción | Qué hace | Por defecto |
|---|---|---|
| `-o archivo.txt` | Nombre del archivo de salida. Con `-o -` muestra el texto en pantalla y no crea archivo | `<id-del-video>.txt` |
| `-p`, `--print` | Además de guardar el archivo, muestra el texto en pantalla | apagado |
| `--langs es en` | Idiomas preferidos para los subtítulos, en orden. Si no existe ninguno, usa el que haya y lo traduce al primero | `es en` |
| `--whisper` | Ignora los subtítulos y transcribe el audio | apagado |
| `--model` | Modelo de Whisper: `tiny`, `base`, `small`, `medium`, `large-v3` | `small` |
| `--cookies-from-browser` | Usa tu sesión de YouTube de `firefox`, `chrome`, `edge` o `brave` | ninguno |

Ver todas: `youtube-transcript --help`

### ¿Qué modelo de Whisper elijo?

| Modelo | Velocidad | Precisión | Cuándo |
|---|---|---|---|
| `tiny` / `base` | Muy rápido | Buena para audio claro | Pruebas, videos largos |
| `small` | Rápido | Muy buena | El día a día (por defecto) |
| `medium` / `large-v3` | Lento en CPU | La mejor | Audio difícil, acentos, ruido |

Como referencia, un video de 9 minutos con `base` tarda alrededor de 1 minuto en una CPU normal. La primera vez que usas un modelo se descarga (de 75 MB a 3 GB según el tamaño).

## Problemas comunes

**"Sign in to confirm you're not a bot" o "YouTube bloqueó la consulta"**
Pasa cuando haces muchas consultas seguidas. Espera un rato (de minutos a una hora) o usa `--cookies-from-browser firefox` con un navegador donde tengas YouTube abierto. En Windows, Chrome y Edge tienen que estar cerrados para leer sus cookies; Firefox suele funcionar mejor.

**"youtube-transcript no se reconoce como comando"**
Abre una terminal nueva después de instalar. Si sigue fallando, vuelve a correr el instalador.

## Desinstalar

- **Windows:** borra `%USERPROFILE%\.youtube-transcript` y quita `%USERPROFILE%\.youtube-transcript\bin` de tu PATH de usuario.
- **macOS / Linux:** `rm -rf ~/.youtube-transcript ~/.local/bin/youtube-transcript`
