"""Local storage discovery and read-only scanning helpers for NEXUS."""

import os
import platform
import shutil
import stat
import string
import time
from pathlib import Path

GIB = 1024 ** 3
MIB = 1024 ** 2

# Only exclude operating-system locations that are not useful or safe to enumerate
# in an ordinary user scan. Development folders and caches remain visible.
DEFAULT_EXCLUDED_DIRS = {
    "$Recycle.Bin",
    "System Volume Information",
    "WindowsApps",
}


def _drive_type(root):
    """Return a readable Windows drive type; unknown on non-Windows systems."""
    if os.name != "nt":
        return "unknown"
    try:
        import ctypes

        value = ctypes.windll.kernel32.GetDriveTypeW(str(root))
        return {
            0: "unknown",
            1: "not_ready",
            2: "removable",
            3: "fixed",
            4: "network",
            5: "optical",
            6: "ram",
        }.get(value, "unknown")
    except (AttributeError, OSError):
        return "unknown"


def _volume_row(root, drive_type="unknown"):
    try:
        total, used, free = shutil.disk_usage(str(root))
    except OSError as exc:
        return None, {"path": str(root), "error": str(exc)}

    system_root = os.environ.get("SystemDrive", "")
    is_system = bool(system_root) and str(root).rstrip("\\\\/").lower() == system_root.rstrip("\\\\/").lower()
    return {
        "drive": str(root),
        "drive_type": drive_type,
        "filesystem": None,
        "is_system": is_system,
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "total_gb": round(total / GIB, 2),
        "used_gb": round(used / GIB, 2),
        "free_gb": round(free / GIB, 2),
        "used_percent": round(used / total * 100, 1) if total else 0,
    }, None


def get_overview():
    """Discover mounted volumes and report capacity without scanning their contents."""
    drives = []
    errors = []

    if os.name == "nt":
        import ctypes

        try:
            logical_mask = ctypes.windll.kernel32.GetLogicalDrives()
        except (AttributeError, OSError):
            logical_mask = 0
        for index, letter in enumerate(string.ascii_uppercase):
            if not (logical_mask & (1 << index)):
                continue
            root = Path(f"{letter}:/")
            drive_type = _drive_type(root)
            row, error = _volume_row(root, drive_type)
            if row:
                drives.append(row)
            if error:
                errors.append(error)
    else:
        try:
            import psutil

            seen = set()
            for partition in psutil.disk_partitions(all=False):
                mountpoint = partition.mountpoint
                if mountpoint in seen:
                    continue
                seen.add(mountpoint)
                row, error = _volume_row(mountpoint, "mounted")
                if row:
                    row["filesystem"] = partition.fstype or None
                    row["device"] = partition.device
                    drives.append(row)
                if error:
                    errors.append(error)
        except (ImportError, OSError):
            row, error = _volume_row(Path("/"), "mounted")
            if row:
                drives.append(row)
            if error:
                errors.append(error)

    drives.sort(key=lambda item: (not item["is_system"], item["drive"]))
    return {
        "drives": drives,
        "platform": platform.platform(),
        "errors": errors,
        "complete": not errors,
    }


def _walk_path(path, max_depth=None, excluded_dirs=None, progress_callback=None, cancel_event=None):
    """Walk without following symlinks; expose counters and cooperative cancellation."""
    base = Path(path)
    excluded = DEFAULT_EXCLUDED_DIRS if excluded_dirs is None else set(excluded_dirs)
    totals = {
        "bytes": 0, "files": 0, "directories": 0, "errors": [],
        "excluded_directories": [], "skipped_symlinks": 0, "cancelled": False,
    }
    last_report = time.monotonic()

    def onerror(error):
        totals["errors"].append({
            "path": getattr(error, "filename", None) or str(base),
            "error": str(error),
        })

    def report(force=False):
        nonlocal last_report
        now = time.monotonic()
        if progress_callback and (force or now - last_report >= 0.25):
            progress_callback({
                "bytes": totals["bytes"], "files": totals["files"],
                "directories": totals["directories"], "errors": len(totals["errors"]),
            })
            last_report = now

    if not base.exists():
        totals["errors"].append({"path": str(base), "error": "La ruta no existe o no es accesible."})
        report(True)
        return totals
    if not base.is_dir():
        totals["errors"].append({"path": str(base), "error": "La ruta seleccionada no es una carpeta."})
        report(True)
        return totals

    try:
        base_depth = len(base.parts)
        for current, dirs, files in os.walk(base, topdown=True, followlinks=False, onerror=onerror):
            if cancel_event and cancel_event.is_set():
                totals["cancelled"] = True
                break
            current_path = Path(current)
            depth = len(current_path.parts) - base_depth
            totals["directories"] += 1
            kept_dirs = []
            for name in dirs:
                child = current_path / name
                if name in excluded:
                    totals["excluded_directories"].append(str(child))
                elif child.is_symlink():
                    totals["skipped_symlinks"] += 1
                elif max_depth is not None and depth >= max_depth:
                    totals["excluded_directories"].append(str(child))
                else:
                    kept_dirs.append(name)
            dirs[:] = kept_dirs

            for name in files:
                if cancel_event and cancel_event.is_set():
                    totals["cancelled"] = True
                    break
                item = current_path / name
                try:
                    if item.is_symlink():
                        totals["skipped_symlinks"] += 1
                        continue
                    stat = item.stat(follow_symlinks=False)
                    if item.is_file():
                        totals["bytes"] += stat.st_size
                        totals["files"] += 1
                        report()
                except OSError as exc:
                    totals["errors"].append({"path": str(item), "error": str(exc)})
                    report()
            report()
            if totals["cancelled"]:
                break
    except OSError as exc:
        totals["errors"].append({"path": str(base), "error": str(exc)})

    report(True)
    return totals


def folder_size(path, max_depth=None):
    """Backward-compatible byte count; defaults to a full recursive scan."""
    return _walk_path(path, max_depth=max_depth)["bytes"]


def scan_system(max_depth=None, progress_callback=None, cancel_event=None):
    """Measure common profile folders and report coverage, progress and cancellation."""
    home = Path.home()
    candidates = [
        ("Descargas", home / "Downloads"), ("Escritorio", home / "Desktop"),
        ("Documentos", home / "Documents"), ("Imágenes", home / "Pictures"),
        ("Vídeos", home / "Videos"), ("AppData Local", home / "AppData" / "Local"),
        ("AppData Roaming", home / "AppData" / "Roaming"),
    ]
    onedrive = os.environ.get("OneDrive")
    if onedrive:
        cloud = Path(onedrive)
        candidates.extend([("OneDrive", cloud), ("OneDrive Documentos", cloud / "Documents"),
                           ("OneDrive Imágenes", cloud / "Pictures")])

    rows, errors, excluded = [], [], []
    skipped_symlinks = total_files = total_bytes = total_dirs = 0
    cancelled = False
    seen = set()
    for label, path in candidates:
        if cancel_event and cancel_event.is_set():
            cancelled = True
            break
        try:
            resolved = str(path.resolve())
        except OSError:
            resolved = str(path)
        if resolved in seen or not path.is_dir():
            continue
        seen.add(resolved)
        base_files, base_bytes, base_dirs, base_errors = total_files, total_bytes, total_dirs, len(errors)

        def folder_progress(values):
            if progress_callback:
                progress_callback({
                    "files": base_files + values["files"],
                    "bytes": base_bytes + values["bytes"],
                    "directories": base_dirs + values["directories"],
                    "errors": base_errors + values["errors"],
                })

        stats = _walk_path(path, max_depth=max_depth, progress_callback=folder_progress,
                           cancel_event=cancel_event)
        total_files += stats["files"]
        total_bytes += stats["bytes"]
        total_dirs += stats["directories"]
        errors.extend(stats["errors"])
        excluded.extend(stats["excluded_directories"])
        skipped_symlinks += stats["skipped_symlinks"]
        cancelled = cancelled or stats["cancelled"]
        rows.append({
            "name": label, "path": str(path), "size_bytes": stats["bytes"],
            "size_gb": round(stats["bytes"] / GIB, 2), "files": stats["files"],
            "directories": stats["directories"], "errors": len(stats["errors"]),
            "excluded_directories": len(stats["excluded_directories"]),
        })
        if cancelled:
            break

    rows.sort(key=lambda row: row["size_bytes"], reverse=True)
    return {
        "folders": rows,
        "coverage": {
            "files": total_files, "bytes": total_bytes, "directories": total_dirs,
            "errors": len(errors), "excluded_directories": len(excluded),
            "skipped_symlinks": skipped_symlinks, "cancelled": cancelled,
            "complete": not errors and not excluded and not cancelled,
            "scope": "Carpetas habituales del perfil de usuario; no representa todo el disco.",
        },
        "errors": errors[:100],
        "note": "El análisis es recursivo. Las carpetas excluidas y los errores se contabilizan; los tamaños son bytes lógicos de archivos accesibles.",
    }


def scan_large_files(root=None, min_size_bytes=GIB, limit=100, max_depth=None,
                    progress_callback=None, cancel_event=None):
    """Find large files under a selected root; read-only with progress and cancellation."""
    scan_root = Path(root).expanduser() if root else Path.home()
    if not scan_root.exists() or not scan_root.is_dir():
        return {"files": [], "error": "La ruta seleccionada no existe o no es una carpeta accesible.",
                "coverage": {"complete": False, "errors": 1}}

    threshold = max(0, int(min_size_bytes))
    limit = max(1, min(int(limit), 1000))
    found, errors, excluded = [], [], []
    skipped_symlinks = files_seen = dirs_seen = bytes_seen = 0
    cancelled = False
    last_report = time.monotonic()

    def onerror(error):
        errors.append({"path": getattr(error, "filename", None) or str(scan_root), "error": str(error)})

    def report(force=False):
        nonlocal last_report
        now = time.monotonic()
        if progress_callback and (force or now - last_report >= 0.25):
            progress_callback({"files": files_seen, "directories": dirs_seen,
                               "bytes": bytes_seen, "errors": len(errors)})
            last_report = now

    base_depth = len(scan_root.parts)
    for current, dirs, files in os.walk(scan_root, topdown=True, followlinks=False, onerror=onerror):
        if cancel_event and cancel_event.is_set():
            cancelled = True
            break
        current_path = Path(current)
        depth = len(current_path.parts) - base_depth
        dirs_seen += 1
        kept = []
        for name in dirs:
            child = current_path / name
            if name in DEFAULT_EXCLUDED_DIRS:
                excluded.append(str(child))
            elif child.is_symlink():
                skipped_symlinks += 1
            elif max_depth is not None and depth >= max_depth:
                excluded.append(str(child))
            else:
                kept.append(name)
        dirs[:] = kept

        for name in files:
            if cancel_event and cancel_event.is_set():
                cancelled = True
                break
            item = current_path / name
            try:
                if item.is_symlink():
                    skipped_symlinks += 1
                    continue
                stat = item.stat(follow_symlinks=False)
                if item.is_file():
                    files_seen += 1
                    bytes_seen += stat.st_size
                    if stat.st_size >= threshold:
                        found.append({"name": name, "path": str(item), "size_bytes": stat.st_size,
                                      "size_gb": round(stat.st_size / GIB, 3)})
            except OSError as exc:
                errors.append({"path": str(item), "error": str(exc)})
            report()
        report()
        if cancelled:
            break

    found.sort(key=lambda row: row["size_bytes"], reverse=True)
    report(True)
    return {
        "files": found[:limit],
        "coverage": {
            "root": str(scan_root), "threshold_bytes": threshold, "matched": len(found),
            "returned": min(len(found), limit), "files": files_seen, "directories": dirs_seen,
            "bytes": bytes_seen, "errors": len(errors), "excluded_directories": len(excluded),
            "skipped_symlinks": skipped_symlinks, "cancelled": cancelled,
            "complete": not errors and not excluded and not cancelled,
        },
        "errors": errors[:100],
        "note": "Solo lectura. No se elimina ni modifica ningún archivo.",
    }


# Explicit, allow-listed roots for the in-app file explorer.
def _is_storage_link(path):
    try:
        info = path.lstat()
        attributes = getattr(info, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return stat.S_ISLNK(info.st_mode) or (os.name == "nt" and bool(attributes & reparse_flag))
    except OSError:
        return True


def storage_categories():
    home = Path.home()
    candidates = [
        ("downloads", "Descargas", home / "Downloads", True),
        ("documents", "Documentos", home / "Documents", True),
        ("desktop", "Escritorio", home / "Desktop", True),
        ("pictures", "Imágenes", home / "Pictures", True),
        ("videos", "Vídeos", home / "Videos", True),
        ("music", "Música", home / "Music", True),
        ("appdata_local", "AppData Local", home / "AppData" / "Local", False),
        ("appdata_roaming", "AppData Roaming", home / "AppData" / "Roaming", False),
        ("program_files", "Aplicaciones (Program Files)", Path(os.environ.get("ProgramFiles", "C:/Program Files")), False),
        ("program_files_x86", "Aplicaciones (x86)", Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")), False),
    ]
    result = []
    for category_id, label, path, deletable in candidates:
        try:
            if path.is_dir() and not _is_storage_link(path):
                result.append({"id": category_id, "name": label, "path": str(path),
                               "deletable": deletable})
        except OSError:
            continue
    return result


def _storage_path_without_links(root, relative_path, allow_empty=False):
    """Resolve a relative path while rejecting symlinks/reparse points at every level."""
    if not isinstance(relative_path, str) or len(relative_path) > 2048:
        raise ValueError("La ruta solicitada no es válida.")
    if not relative_path and allow_empty:
        return root, root.stat()
    if not relative_path:
        raise ValueError("Debes indicar un archivo.")
    raw_parts = relative_path.replace("\\", "/").split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("La ruta solicitada no es válida.")
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or any(part in {"..", "."} for part in relative.parts):
        raise ValueError("La ruta solicitada no es válida.")

    current = root
    final_info = None
    for index, part in enumerate(relative.parts):
        current = current / part
        info = current.lstat()
        attributes = getattr(info, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if stat.S_ISLNK(info.st_mode) or (os.name == "nt" and attributes & reparse_flag):
            raise ValueError("No se permite acceder a enlaces simbólicos o puntos de reanálisis.")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ValueError("La ruta intermedia no es una carpeta.")
        final_info = info

    resolved_root = root.resolve(strict=True)
    resolved_target = current.resolve(strict=True)
    if not resolved_target.is_relative_to(resolved_root):
        raise ValueError("No se permite salir de la categoría seleccionada.")
    return current, final_info


def browse_storage_category(category_id, relative_path=""):
    """List one directory under a fixed category root; never follow symlinks."""
    categories = {item["id"]: item for item in storage_categories()}
    category = categories.get(category_id)
    if not category:
        raise ValueError("Categoría no válida o no disponible.")
    root = Path(category["path"]).resolve(strict=True)
    try:
        target, info = _storage_path_without_links(root, relative_path, allow_empty=True)
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError("La ubicación solicitada no es una carpeta.")
        entries = []
        with os.scandir(target) as iterator:
            for entry in iterator:
                try:
                    entry_info = entry.stat(follow_symlinks=False)
                    attributes = getattr(entry_info, "st_file_attributes", 0)
                    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                    if entry.is_symlink() or (os.name == "nt" and attributes & reparse_flag):
                        continue
                    is_dir = stat.S_ISDIR(entry_info.st_mode)
                    if not is_dir and not stat.S_ISREG(entry_info.st_mode):
                        continue
                    entries.append({
                        "name": entry.name,
                        "relative_path": str(Path(relative_path) / entry.name) if relative_path else entry.name,
                        "is_dir": is_dir,
                        "size_bytes": 0 if is_dir else entry_info.st_size,
                        "modified": entry_info.st_mtime,
                    })
                except OSError:
                    continue
        entries.sort(key=lambda item: (not item["is_dir"], -item["size_bytes"], item["name"].casefold()))
        relative = Path(relative_path) if relative_path else Path()
        return {"category": category, "relative_path": relative_path,
                "parent_path": str(relative.parent) if relative.parts else None,
                "entries": entries, "count": len(entries)}
    except (OSError, RuntimeError) as exc:
        raise ValueError("No se pudo leer esta carpeta: " + str(exc)) from exc


def delete_storage_files(category_id, relative_paths):
    """Delete only explicitly selected regular files in user-owned folders."""
    if not isinstance(category_id, str):
        raise ValueError("Categoría no válida.")
    categories = {item["id"]: item for item in storage_categories()}
    category = categories.get(category_id)
    if not category or not category["deletable"]:
        raise ValueError("Esta categoría está protegida y no permite eliminación desde NEXUS.")
    if not isinstance(relative_paths, list) or not relative_paths or len(relative_paths) > 100:
        raise ValueError("Selecciona entre 1 y 100 archivos.")
    root = Path(category["path"]).resolve(strict=True)
    results = []
    for raw in relative_paths:
        if not isinstance(raw, str):
            results.append({"path": str(raw), "status": "rejected"})
            continue
        try:
            target, info = _storage_path_without_links(root, raw)
            if not stat.S_ISREG(info.st_mode):
                results.append({"path": raw, "status": "rejected"})
                continue
            size = info.st_size
            # Unlink the validated path itself, not its resolved target.
            target.unlink()
            results.append({"path": raw, "status": "deleted", "bytes_freed": size})
        except ValueError:
            results.append({"path": raw, "status": "rejected"})
        except OSError as exc:
            results.append({"path": raw, "status": "error", "error": str(exc)})
    return {"results": results, "deleted": sum(x["status"] == "deleted" for x in results),
            "bytes_freed": sum(x.get("bytes_freed", 0) for x in results)}
