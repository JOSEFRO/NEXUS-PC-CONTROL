"""Read-only duplicate discovery using size grouping followed by SHA-256 verification."""
import hashlib
import os
import stat
import time
from pathlib import Path

CHUNK_SIZE = 1024 * 1024
MAX_FILES = 500_000
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".heic"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf", ".odt"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"}
CATEGORIES = {
    "images": IMAGE_EXTENSIONS, "documents": DOCUMENT_EXTENSIONS,
    "videos": VIDEO_EXTENSIONS, "audio": AUDIO_EXTENSIONS,
}


def _is_reparse_or_link(info):
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or (os.name == "nt" and bool(getattr(info, "st_file_attributes", 0) & flag))


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def scan_duplicates(roots, category="all", min_size_bytes=1, cancel_event=None, progress_callback=None):
    """Find byte-identical files. Never follows links and never deletes or moves data."""
    if not isinstance(roots, (list, tuple)) or not roots or len(roots) > 20:
        raise ValueError("Selecciona entre 1 y 20 carpetas.")
    if category != "all" and category not in CATEGORIES:
        raise ValueError("Categoría de archivos no válida.")
    min_size_bytes = max(1, min(int(min_size_bytes), 1024 ** 4))
    allowed_extensions = None if category == "all" else CATEGORIES[category]
    size_groups = {}
    errors = []
    files_seen = bytes_seen = hashed_files = 0
    last_report = time.monotonic()

    def report(force=False):
        nonlocal last_report
        now = time.monotonic()
        if progress_callback and (force or now - last_report >= 0.25):
            progress_callback({"files": files_seen, "bytes": bytes_seen,
                               "hashed_files": hashed_files, "errors": len(errors)})
            last_report = now

    for raw_root in roots:
        root = Path(raw_root).expanduser()
        try:
            root_info = root.lstat()
            if _is_reparse_or_link(root_info) or not stat.S_ISDIR(root_info.st_mode):
                errors.append({"path": str(root), "error": "La carpeta no es válida o es un enlace."})
                continue
            root = root.resolve(strict=True)
        except OSError as exc:
            errors.append({"path": str(root), "error": str(exc)})
            continue

        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            if cancel_event and cancel_event.is_set():
                report(True)
                return _result(size_groups, errors, files_seen, bytes_seen, hashed_files, True)
            current_path = Path(current)
            safe_dirs = []
            for name in dirs:
                child = current_path / name
                try:
                    info = child.lstat()
                    if not _is_reparse_or_link(info) and stat.S_ISDIR(info.st_mode):
                        safe_dirs.append(name)
                except OSError as exc:
                    errors.append({"path": str(child), "error": str(exc)})
            dirs[:] = safe_dirs

            for name in files:
                if cancel_event and cancel_event.is_set():
                    report(True)
                    return _result(size_groups, errors, files_seen, bytes_seen, hashed_files, True)
                item = current_path / name
                try:
                    info = item.lstat()
                    if _is_reparse_or_link(info) or not stat.S_ISREG(info.st_mode):
                        continue
                    if info.st_size < min_size_bytes:
                        continue
                    if allowed_extensions is not None and item.suffix.lower() not in allowed_extensions:
                        continue
                    files_seen += 1
                    bytes_seen += info.st_size
                    size_groups.setdefault(info.st_size, []).append(str(item))
                    if files_seen >= MAX_FILES:
                        errors.append({"path": str(root), "error": "Se alcanzó el límite de seguridad de archivos analizados."})
                        return _result(size_groups, errors, files_seen, bytes_seen, hashed_files, False)
                except OSError as exc:
                    errors.append({"path": str(item), "error": str(exc)})
                report()

    duplicates = []
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue
        hash_groups = {}
        for raw_path in paths:
            if cancel_event and cancel_event.is_set():
                report(True)
                return _result_from_groups(hash_groups, errors, files_seen, bytes_seen, hashed_files, True)
            path = Path(raw_path)
            try:
                before = path.lstat()
                if _is_reparse_or_link(before) or not stat.S_ISREG(before.st_mode):
                    continue
                digest = _digest(path)
                after = path.lstat()
                if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                    errors.append({"path": raw_path, "error": "El archivo cambió durante el análisis; se omitió."})
                    continue
                hash_groups.setdefault(digest, []).append({"path": raw_path, "size_bytes": size})
                hashed_files += 1
            except OSError as exc:
                errors.append({"path": raw_path, "error": str(exc)})
            report()
        duplicates.extend(group for group in hash_groups.values() if len(group) > 1)

    report(True)
    return {"groups": duplicates, "duplicate_groups": len(duplicates),
            "duplicate_files": sum(len(group) for group in duplicates),
            "potential_waste_bytes": sum((len(group) - 1) * group[0]["size_bytes"] for group in duplicates),
            "files_scanned": files_seen, "bytes_observed": bytes_seen,
            "files_hashed": hashed_files, "errors": errors[:100], "cancelled": False,
            "method": "SHA-256 exact-content comparison",
            "note": "Solo lectura. No se elimina ni modifica ningún archivo."}


def _result(size_groups, errors, files_seen, bytes_seen, hashed_files, cancelled):
    # A cancellation during enumeration has no verified duplicate groups yet.
    return {"groups": [], "duplicate_groups": 0, "duplicate_files": 0,
            "potential_waste_bytes": 0, "files_scanned": files_seen,
            "bytes_observed": bytes_seen, "files_hashed": hashed_files,
            "errors": errors[:100], "cancelled": cancelled,
            "method": "SHA-256 exact-content comparison",
            "note": "Resultado parcial: el análisis se canceló antes de verificar todos los grupos."}


def _result_from_groups(groups, errors, files_seen, bytes_seen, hashed_files, cancelled):
    found = [group for group in groups.values() if len(group) > 1]
    return {"groups": found, "duplicate_groups": len(found),
            "duplicate_files": sum(len(group) for group in found),
            "potential_waste_bytes": sum((len(group) - 1) * group[0]["size_bytes"] for group in found),
            "files_scanned": files_seen, "bytes_observed": bytes_seen,
            "files_hashed": hashed_files, "errors": errors[:100], "cancelled": cancelled,
            "method": "SHA-256 exact-content comparison",
            "note": "Resultado parcial: el análisis se canceló durante la verificación."}
