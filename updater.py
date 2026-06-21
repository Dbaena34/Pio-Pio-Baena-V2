import urllib.request
import json
import os
import sys

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
GITHUB_USER = "Dbaena34"
GITHUB_REPO = "Pio-Pio-Baena-V2"
BRANCH      = "main"

RAW_BASE    = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
API_BASE    = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/git/trees/{BRANCH}?recursive=1"

VERSION_FILE = "version.txt"

# Archivos/carpetas que nunca se sobreescriben en la máquina del usuario
EXCLUDED = {
    ".venv", ".git", "__pycache__",
    "iniciar.bat", "instalar.bat", "backup.bat",
    "updater.py",
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def leer_version_local():
    if not os.path.exists(VERSION_FILE):
        return "0.0"
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def leer_version_remota():
    url = f"{RAW_BASE}/{VERSION_FILE}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode("utf-8").strip()
    except Exception:
        return None

def obtener_arbol_remoto():
    """Devuelve lista de rutas de archivos en el repo (sin carpetas)."""
    try:
        req = urllib.request.Request(API_BASE, headers={"User-Agent": "PioPioUpdater"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]
    except Exception:
        return []

def descargar_archivo(ruta_remota):
    url = f"{RAW_BASE}/{ruta_remota}"
    try:
        # Crear carpetas intermedias si no existen
        carpeta = os.path.dirname(ruta_remota)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)

        req = urllib.request.Request(url, headers={"User-Agent": "PioPioUpdater"})
        with urllib.request.urlopen(req, timeout=15) as r:
            contenido = r.read()

        with open(ruta_remota, "wb") as f:
            f.write(contenido)
        return True
    except Exception:
        return False

def excluir(ruta):
    partes = ruta.replace("\\", "/").split("/")
    return partes[0] in EXCLUDED

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("  Verificando actualizaciones...")

    version_local  = leer_version_local()
    version_remota = leer_version_remota()

    if version_remota is None:
        print("  No se pudo conectar con el servidor. Continuando sin actualizar.")
        print()
        return

    if version_local == version_remota:
        print(f"  Sistema actualizado (v{version_local})")
        print()
        return

    print()
    print(f"  Nueva version disponible: v{version_remota}  (actual: v{version_local})")
    print("  Actualizando sistema, por favor espere...")
    print()

    archivos = obtener_arbol_remoto()
    if not archivos:
        print("  Error al obtener lista de archivos. Continuando sin actualizar.")
        print()
        return

    errores = []
    for ruta in archivos:
        if excluir(ruta):
            continue
        ok = descargar_archivo(ruta)
        if ok:
            print(f"    Actualizado: {ruta}")
        else:
            errores.append(ruta)

    print()
    if errores:
        print(f"  Advertencia: {len(errores)} archivo(s) no pudieron actualizarse:")
        for e in errores:
            print(f"    - {e}")
    else:
        print(f"  Actualizacion completada exitosamente. Version: v{version_remota}")

    print()

if __name__ == "__main__":
    main()
