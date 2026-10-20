"""Instala dependencias que falten al momento de usarlas."""
import importlib
import importlib.util
import subprocess
import sys


def ensure(*pkgs: tuple[str, str]) -> None:
    """pkgs: pares (modulo_import, nombre_pip). Instala con pip los que falten."""
    missing = [pip for mod, pip in pkgs if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    print(f"[setup] Falta {', '.join(missing)}; instalando...", file=sys.stderr)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])
    except subprocess.CalledProcessError:
        sys.exit(
            f"[setup] No pude instalar {', '.join(missing)}. "
            f"Instalalo a mano: {sys.executable} -m pip install {' '.join(missing)}"
        )
    importlib.invalidate_caches()
