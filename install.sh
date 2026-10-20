#!/usr/bin/env sh
# Instalador de youtube-transcript para macOS y Linux.
# Detecta Python (lo instala con brew/apt/dnf/pacman/zypper/apk si falta), crea un
# entorno aislado en ~/.youtube-transcript y deja el comando `youtube-transcript` en ~/.local/bin.
#
# Desde una copia del repo:   sh install.sh
# Sin clonar:                 curl -fsSL https://raw.githubusercontent.com/Juanpablo9717/youtube-transcript/main/install.sh | sh
# Sin Whisper (mas liviano):  sh install.sh --sin-audio
set -eu

REPO="https://github.com/Juanpablo9717/youtube-transcript"
PREFIX="$HOME/.youtube-transcript"
VENV="$PREFIX/venv"
BIN="$HOME/.local/bin"
EXTRA="[audio]"
[ "${1:-}" = "--sin-audio" ] && EXTRA=""

say() { printf '\033[36m[youtube-transcript]\033[0m %s\n' "$*"; }
die() { printf '\033[31m[youtube-transcript]\033[0m %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 && SUDO="sudo"
fi

find_python() {
    for c in python3 python python3.13 python3.12 python3.11 python3.10 python3.9; do
        if command -v "$c" >/dev/null 2>&1 &&
           "$c" -c 'import sys, venv, ensurepip; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
            echo "$c"; return 0
        fi
    done
    return 1
}

install_python() {
    case "$(uname -s)" in
        Darwin)
            command -v brew >/dev/null 2>&1 ||
                die "Falta Homebrew. Instalalo desde https://brew.sh o instala Python desde https://www.python.org/downloads/"
            brew install python@3.12 ;;
        Linux)
            if   command -v apt-get >/dev/null 2>&1; then $SUDO apt-get update -qq && $SUDO apt-get install -y python3 python3-venv python3-pip
            elif command -v dnf     >/dev/null 2>&1; then $SUDO dnf install -y python3 python3-pip
            elif command -v pacman  >/dev/null 2>&1; then $SUDO pacman -Sy --noconfirm python python-pip
            elif command -v zypper  >/dev/null 2>&1; then $SUDO zypper install -y python3 python3-pip
            elif command -v apk     >/dev/null 2>&1; then $SUDO apk add python3 py3-pip
            else die "No reconozco tu gestor de paquetes. Instala Python 3.9+ y vuelve a correr el script."
            fi ;;
        *) die "Sistema no soportado: $(uname -s). En Windows usa install.ps1." ;;
    esac
}

# 1. Python
PY="$(find_python || true)"
if [ -z "$PY" ]; then
    say "No encontre Python 3.9+ con venv. Instalandolo..."
    install_python
    hash -r 2>/dev/null || true
    PY="$(find_python || true)"
    [ -n "$PY" ] || die "Python se instalo pero no lo encuentro. Abre una terminal nueva y vuelve a correr el script."
fi
say "Python $("$PY" -c 'import sys; print(sys.version.split()[0])') -> $(command -v "$PY")"

# 2. Entorno aislado (evita el error 'externally-managed-environment' de Debian/Ubuntu/Homebrew)
if [ ! -x "$VENV/bin/python" ]; then
    say "Creando entorno en $VENV"
    "$PY" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install --quiet --upgrade pip

# 3. Paquete (desde la copia local si existe, si no desde GitHub)
SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    SPEC="$SCRIPT_DIR$EXTRA"
else
    SPEC="youtube-transcript$EXTRA @ $REPO/archive/refs/heads/main.zip"
fi
say "Instalando dependencias (la primera vez puede tardar unos minutos)..."
"$VENV/bin/python" -m pip install --quiet --upgrade "$SPEC"

# 4. Comando en el PATH
mkdir -p "$BIN"
ln -sf "$VENV/bin/youtube-transcript" "$BIN/youtube-transcript"
case ":$PATH:" in
    *":$BIN:"*) ;;
    *)
        for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
            if [ -f "$rc" ] && ! grep -q '.local/bin' "$rc"; then
                printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
                say "Agregue ~/.local/bin al PATH en $rc"
            fi
        done
        say "Abre una terminal nueva (o corre: export PATH=\"\$HOME/.local/bin:\$PATH\")" ;;
esac

say "Listo. Prueba:  youtube-transcript \"https://www.youtube.com/watch?v=...\""
