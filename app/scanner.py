import os, shutil, platform, string
from pathlib import Path

SKIP_DIRS = {"$Recycle.Bin", "System Volume Information", "WindowsApps", "node_modules", ".git"}

def get_overview():
    drives = []
    if os.name == "nt":
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:/")
            if root.exists():
                try:
                    total, used, free = shutil.disk_usage(str(root))
                    drives.append({"drive": f"{letter}:", "total_gb": round(total/1024**3,1),
                        "used_gb": round(used/1024**3,1), "free_gb": round(free/1024**3,1),
                        "used_percent": round(used/total*100,1) if total else 0})
                except OSError:
                    pass
    else:
        total, used, free = shutil.disk_usage("/")
        drives.append({"drive": "/", "total_gb": round(total/1024**3,1),
            "used_gb": round(used/1024**3,1), "free_gb": round(free/1024**3,1),
            "used_percent": round(used/total*100,1)})
    return {"drives": drives, "platform": platform.platform()}

def folder_size(path, max_depth=2):
    total = 0
    try:
        base_depth = len(Path(path).parts)
        for current, dirs, files in os.walk(path):
            depth = len(Path(current).parts) - base_depth
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if depth >= max_depth:
                dirs[:] = []
            for name in files:
                try:
                    total += (Path(current)/name).stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total

def scan_system():
    home = Path.home()
    candidates = [
        ("Perfil de usuario", home), ("Descargas", home/"Downloads"),
        ("Escritorio", home/"Desktop"), ("Documentos", home/"Documents"),
        ("Imágenes", home/"Pictures"), ("Vídeos", home/"Videos"),
        ("AppData Local", home/"AppData"/"Local"),
        ("Temp de usuario", Path(os.environ.get("TEMP", str(home/"AppData/Local/Temp")))),
    ]
    rows = []
    for label, path in candidates:
        if path.exists():
            rows.append({"name": label, "path": str(path),
                         "size_gb": round(folder_size(path)/1024**3,2)})
    rows.sort(key=lambda x: x["size_gb"], reverse=True)
    return {"folders": rows, "note": "Estimación de profundidad limitada; los tamaños pueden solaparse."}

def scan_large_files():
    root = Path.home()
    found = []
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            p = Path(current)/name
            try:
                size = p.stat().st_size
                if size >= 1024**3:
                    found.append({"name": name, "path": str(p), "size_gb": round(size/1024**3,2)})
            except OSError:
                pass
    found.sort(key=lambda x: x["size_gb"], reverse=True)
    return {"files": found[:100], "note": "Solo perfil de usuario; no se elimina ningún archivo."}
