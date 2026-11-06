import platform
from flask import Flask, jsonify, render_template, request
from .scanner import get_overview, scan_system, scan_large_files
from .cleaner import get_cleanup_candidates, clean_selected

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/overview")
def overview():
    return jsonify(get_overview())

@app.get("/api/scan")
def scan():
    return jsonify(scan_system())

@app.get("/api/large-files")
def large_files():
    return jsonify(scan_large_files())

@app.get("/api/cleanup")
def cleanup_candidates():
    return jsonify(get_cleanup_candidates())

@app.post("/api/cleanup")
def cleanup():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
        return jsonify({"error": "Selección inválida"}), 400
    return jsonify(clean_selected(ids))

@app.get("/api/health")
def health():
    import psutil
    vm = psutil.virtual_memory()
    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=0.4),
        "ram_percent": vm.percent,
        "ram_total_gb": round(vm.total / 1024**3, 1),
        "ram_available_gb": round(vm.available / 1024**3, 1),
        "python": platform.python_version(),
        "windows": platform.platform()
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
