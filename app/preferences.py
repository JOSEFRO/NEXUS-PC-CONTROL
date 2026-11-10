"""Safe, local NEXUS preferences with schema validation and atomic persistence."""
import json
import os
import tempfile
from pathlib import Path

DEFAULTS = {
    "appearance": {"theme": "dark", "accent": "electric-green", "compact_mode": False},
    "language": "es",
    "modules": {
        "storage": True, "duplicates": True, "app_manager": True,
        "cleaner": True, "system_health": True,
    },
    "scanning": {
        "include_hidden": False, "follow_links": False,
        "duplicate_min_size_bytes": 1, "duplicate_hash": "sha256",
    },
    "notifications": {"scan_complete": True, "warnings": True},
}
ALLOWED_THEMES = {"dark", "light", "system"}
ALLOWED_LANGUAGES = {"es", "en"}
MODULES = set(DEFAULTS["modules"])
MAX_SETTINGS_BYTES = 64 * 1024


def settings_path():
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    return base / "NEXUS-PC-CONTROL" / "settings.json"


def _merge_known(default, supplied):
    if not isinstance(supplied, dict):
        return default
    result = dict(default)
    for key, value in supplied.items():
        if key not in default:
            continue
        if isinstance(default[key], dict):
            result[key] = _merge_known(default[key], value)
        elif isinstance(default[key], bool) and isinstance(value, bool):
            result[key] = value
        elif isinstance(default[key], int) and not isinstance(default[key], bool) and isinstance(value, int):
            result[key] = max(1, min(value, 1024 ** 4))
        elif isinstance(default[key], str) and isinstance(value, str):
            result[key] = value
    return result


def get_settings():
    path = settings_path()
    try:
        if path.stat().st_size > MAX_SETTINGS_BYTES:
            raise ValueError("El archivo de configuración supera el tamaño permitido.")
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    except (OSError, ValueError, json.JSONDecodeError):
        data = {}
    settings = _merge_known(DEFAULTS, data)
    if settings["appearance"]["theme"] not in ALLOWED_THEMES:
        settings["appearance"]["theme"] = DEFAULTS["appearance"]["theme"]
    if settings["language"] not in ALLOWED_LANGUAGES:
        settings["language"] = "es"
    settings["scanning"]["follow_links"] = False
    settings["scanning"]["duplicate_hash"] = "sha256"
    return settings


def update_settings(patch):
    if not isinstance(patch, dict):
        raise ValueError("La configuración debe ser un objeto.")
    current = get_settings()
    merged = _merge_known(current, patch)
    if merged["appearance"]["theme"] not in ALLOWED_THEMES:
        raise ValueError("Tema no válido.")
    if merged["language"] not in ALLOWED_LANGUAGES:
        raise ValueError("Idioma no válido.")
    merged["scanning"]["follow_links"] = False
    merged["scanning"]["duplicate_hash"] = "sha256"
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(merged, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
    return merged
