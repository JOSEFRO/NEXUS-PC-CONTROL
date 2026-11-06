import os, tempfile
from pathlib import Path

ALLOWED = {"user_temp", "windows_temp", "crash_dumps"}

def size_of(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            try: total += (Path(root)/name).stat().st_size
            except OSError: pass
    return total

def get_cleanup_candidates():
    temp = Path(os.environ.get("TEMP", tempfile.gettempdir()))
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home()/"AppData/Local")))
    entries = [
        {"id":"user_temp","name":"Temporales del usuario","path":str(temp),
         "description":"Temporales de sesión; archivos bloqueados se omiten."},
        {"id":"windows_temp","name":"Temporales de Windows","path":str(Path(os.environ.get("WINDIR","C:/Windows"))/"Temp"),
         "description":"Puede requerir permisos elevados."},
        {"id":"crash_dumps","name":"Informes de errores","path":str(local/"CrashDumps"),
         "description":"Volcados de fallos de aplicaciones."}
    ]
    out = []
    for e in entries:
        p = Path(e["path"])
        if p.exists():
            e["size_mb"] = round(size_of(p)/1024**2,1)
            out.append(e)
    return {"items":out,"warning":"No incluye carpetas personales, juegos ni máquinas virtuales."}

def clean_selected(ids):
    candidates = {x["id"]:x for x in get_cleanup_candidates()["items"]}
    results = []
    for item_id in ids:
        if item_id not in ALLOWED or item_id not in candidates:
            results.append({"id":item_id,"status":"rechazado"})
            continue
        base = Path(candidates[item_id]["path"]).resolve()
        deleted = errors = 0
        for root, dirs, files in os.walk(base, topdown=False):
            for name in files:
                p = Path(root)/name
                try:
                    if p.is_symlink() or not p.resolve().is_relative_to(base): continue
                    p.unlink(); deleted += 1
                except OSError:
                    errors += 1
            for name in dirs:
                p = Path(root)/name
                try:
                    if not p.is_symlink() and p.resolve().is_relative_to(base): p.rmdir()
                except OSError:
                    pass
        results.append({"id":item_id,"status":"completado","archivos_eliminados":deleted,"omitidos":errors})
    return {"results":results,"message":"Archivos en uso o sin permisos fueron omitidos."}
