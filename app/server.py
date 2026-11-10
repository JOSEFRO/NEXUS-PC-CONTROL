import platform
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, render_template, request
from .scanner import get_overview, scan_system, scan_large_files, storage_categories, browse_storage_category, delete_storage_files, MIB, GIB
from .cleaner import get_cleanup_candidates, clean_selected
from .scan_jobs import scan_jobs\nfrom .preferences import get_settings, update_settings

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


def _optional_int(name, default, minimum, maximum):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        abort(400, description=f"El parámetro {name} debe ser un número entero.")
    if value < minimum or value > maximum:
        abort(400, description=f"El parámetro {name} está fuera del rango permitido.")
    return value


@app.before_request
def allow_local_host_only():
    # Prevent a remote webpage from reaching the local service through DNS rebinding.
    hostname = (urlsplit("//" + request.host).hostname or "").lower()
    if hostname not in {"127.0.0.1", "localhost", "::1"}:
        abort(403)


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/overview")
def overview():
    return jsonify(get_overview())


@app.get("/api/scan")
def scan():
    max_depth = request.args.get("max_depth")
    if max_depth is not None:
        max_depth = _optional_int("max_depth", None, 0, 64)
    return jsonify(scan_system(max_depth=max_depth))


@app.get("/api/large-files")
def large_files():
    threshold_mb = _optional_int("min_size_mb", 1024, 1, 1024 * 1024)
    limit = _optional_int("limit", 100, 1, 1000)
    max_depth = request.args.get("max_depth")
    if max_depth is not None:
        max_depth = _optional_int("max_depth", None, 0, 64)
    root = request.args.get("root") or None
    return jsonify(scan_large_files(
        root=root,
        min_size_bytes=threshold_mb * MIB,
        limit=limit,
        max_depth=max_depth,
    ))


@app.post("/api/storage/scans")
def start_storage_scan():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Solicitud inválida."}), 400
    kind = payload.get("kind", "profile")
    if kind not in {"profile", "large_files"}:
        return jsonify({"error": "Tipo de análisis no válido."}), 400
    options = {}
    if "max_depth" in payload and payload["max_depth"] is not None:
        try:
            depth = int(payload["max_depth"])
        except (TypeError, ValueError):
            return jsonify({"error": "max_depth debe ser un entero."}), 400
        if depth < 0 or depth > 64:
            return jsonify({"error": "max_depth está fuera del rango permitido."}), 400
        options["max_depth"] = depth
    if kind == "large_files":
        try:
            threshold_mb = int(payload.get("min_size_mb", 1024))
            limit = int(payload.get("limit", 100))
        except (TypeError, ValueError):
            return jsonify({"error": "El tamaño y el límite deben ser números enteros."}), 400
        if threshold_mb < 1 or threshold_mb > 1024 * 1024 or limit < 1 or limit > 1000:
            return jsonify({"error": "El tamaño o el límite están fuera del rango permitido."}), 400
        root = payload.get("root")
        if root is not None and (not isinstance(root, str) or not root.strip() or len(root) > 2048):
            return jsonify({"error": "La ruta indicada no es válida."}), 400
        options.update({"min_size_bytes": threshold_mb * MIB, "limit": limit, "root": root or None})
    try:
        return jsonify(scan_jobs.start(kind, options)), 202
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 429


@app.get("/api/storage/scans/<scan_id>")
def get_storage_scan(scan_id):
    job = scan_jobs.get(scan_id)
    if job is None:
        return jsonify({"error": "No se encontró ese análisis o ya expiró."}), 404
    return jsonify(job)


@app.post("/api/storage/scans/<scan_id>/cancel")
def cancel_storage_scan(scan_id):
    job = scan_jobs.cancel(scan_id)
    if job is None:
        return jsonify({"error": "No se encontró ese análisis o ya expiró."}), 404
    return jsonify(job), 202




@app.get("/api/storage/categories")
def storage_category_list():
    return jsonify({"categories": storage_categories()})


@app.get("/api/storage/browse/<category_id>")
def storage_browse(category_id):
    relative_path = request.args.get("path", "")
    if len(relative_path) > 2048:
        return jsonify({"error": "La ruta es demasiado larga."}), 400
    try:
        return jsonify(browse_storage_category(category_id, relative_path))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/storage/delete")
def storage_delete():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Solicitud inválida."}), 400
    category_id = payload.get("category")
    paths = payload.get("paths")
    try:
        result = delete_storage_files(category_id, paths)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/settings")
def settings_get():
    return jsonify(get_settings())


@app.put("/api/settings")
def settings_put():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "La configuración debe ser un objeto JSON."}), 400
    try:
        return jsonify(update_settings(payload))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/storage/duplicates")
def start_duplicate_scan():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Solicitud inválida."}), 400
    category_id = payload.get("category", "downloads")
    allowed = {item["id"]: item for item in storage_categories() if item["deletable"]}
    category = allowed.get(category_id)
    if not category:
        return jsonify({"error": "Selecciona una carpeta personal admitida para analizar."}), 400
    kind = payload.get("file_category", "all")
    if kind not in {"all", "images", "documents", "videos", "audio"}:
        return jsonify({"error": "Tipo de archivo no válido."}), 400
    try:
        min_size = int(payload.get("min_size_bytes", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "El tamaño mínimo debe ser un entero."}), 400
    if min_size < 1 or min_size > 1024 ** 4:
        return jsonify({"error": "El tamaño mínimo está fuera del rango permitido."}), 400
    try:
        return jsonify(scan_jobs.start("duplicates", {
            "root": category["path"], "file_category": kind, "min_size_bytes": min_size
        })), 202
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 429

@app.get("/api/cleanup")
def cleanup_candidates():
    return jsonify(get_cleanup_candidates())


@app.post("/api/cleanup")
def cleanup():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        return jsonify({"error": "Selección inválida"}), 400
    if len(ids) > 3:
        return jsonify({"error": "La selección supera las categorías permitidas"}), 400
    return jsonify(clean_selected(ids))


@app.get("/api/health")
def health():
    import psutil

    vm = psutil.virtual_memory()
    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=0.4),
        "ram_percent": vm.percent,
        "ram_total_gb": round(vm.total / GIB, 1),
        "ram_available_gb": round(vm.available / GIB, 1),
        "python": platform.python_version(),
        "windows": platform.platform()
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
