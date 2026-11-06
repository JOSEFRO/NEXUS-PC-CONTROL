import os
import platform
import shutil
import string
from pathlib import Path

SKIP_DIRS = {
    "$Recycle.Bin", "System Volume Information", "WindowsApps",
    "node_modules", ".git", "__pycache__"
}
GIB = 1024 ** 3


def get_overview():
    drives = []
    if os.name == "nt":
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:/")
            if root.exists():
                try:
                    total, used, free = shutil.disk_usage(str(root))
                    drives.append({
                        "drive": f"{letter}:",
                        "total_gb": round(total / GIB, 1),
                        "used_gb": round(used / GIB, 1),
                        "free_gb": round(free / GIB, 1),
                        "used_percent": round(used / total * 100, 1) if total else 0,
                    })
                except OSError:
                    continue
    else:
        total, used, free = shutil.disk_usage("/")
        drives.append({
            "drive": "/",
            "total_gb": round(total / GIB, 1),
            "used_gb": round(used / GIB, 1),
            "free_gb": round(free / GIB, 1),
            "used_percent": round(used / total * 100, 1) if total else 0,
        })
    return {"drives": drives, "platform": platform.platform()}


def folder_size(path, max_depth=4):
    total = 0
    path = Path(path)
    try:
        base_depth = len(path.parts)
        for current, dirs, files in os.walk(path, followlinks=False):
            depth = len(Path(current).parts) - base_depth
            dirs[:] = [
                name for name in dirs
                if name not in SKIP_DIRS and not (Path(current) / name).is_symlink()
            ]
            if depth >= max_depth:
                dirs[:] = []
            for name in files:
                item = Path(current) / name
                try:
                    if not item.is_symlink():
                        total += item.stat().st_size
                except OSError:
                    continue
    except OSError:
        pass
    return total


def scan_system():
    home = Path.home()
    candidates = [
        ("Descargas", home / "Downloads"),
        ("Escritorio", home / "Desktop"),
        ("Documentos", home / "Documents"),
        ("Imágenes", home / "Pictures"),
        ("Vídeos", home / "Videos"),
        ("AppData Local", home / "AppData" / "Local"),
        ("AppData Roaming", home / "AppData" / "Roaming"),
    ]
    rows = []
    for label, path in candidates:
        if path.exists():
            rows.append({
                "name": label,
                "path": str(path),
                "size_gb": round(folder_size(path) / GIB, 2),
            })
    rows.sort(key=lambda row: row["size_gb"], reverse=True)
    return {
        "folders": rows,
        "note": "Escaneo limitado a carpetas seleccionadas. Los tamaños son aproximados y pueden omitir archivos protegidos."
    }


def scan_large_files():
    root = Path.home()
    found = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [
            name for name in dirs
            if name not in SKIP_DIRS and not (Path(current) / name).is_symlink()
        ]
        for name in files:
            item = Path(current) / name
            try:
                if item.is_symlink():
                    continue
                size = item.stat().st_size
                if size >= GIB:
                    found.append({
                        "name": name,
                        "path": str(item),
                        "size_gb": round(size / GIB, 2),
                    })
            except OSError:
                continue
    found.sort(key=lambda row: row["size_gb"], reverse=True)
    return {
        "files": found[:100],
        "note": "Solo se inspecciona el perfil del usuario. No se elimina ningún archivo."
    }
