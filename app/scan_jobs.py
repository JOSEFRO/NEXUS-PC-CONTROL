"""In-process background scan jobs for the local NEXUS service."""

from __future__ import annotations

import threading
import time
import uuid
from copy import deepcopy

from .scanner import scan_system, scan_large_files\nfrom .duplicates import scan_duplicates

TERMINAL = {"cancelled", "completed", "completed_with_warnings", "failed"}


class ScanJobManager:
    """Thread-safe manager for bounded, read-only background scan tasks."""

    def __init__(self, max_jobs=2, retention_seconds=3600):
        self._lock = threading.RLock()
        self._jobs = {}
        self._max_jobs = max_jobs
        self._retention_seconds = retention_seconds

    def _prune(self):
        cutoff = time.time() - self._retention_seconds
        for job_id, job in list(self._jobs.items()):
            if job["status"] in TERMINAL and job.get("finished_at", 0) < cutoff:
                self._jobs.pop(job_id, None)

    def start(self, kind, options=None):
        options = dict(options or {})
        with self._lock:
            self._prune()
            active = sum(job["status"] in {"queued", "running", "cancelling"} for job in self._jobs.values())
            if active >= self._max_jobs:
                raise RuntimeError("Ya hay demasiados análisis activos. Espera a que termine uno.")
            job_id = uuid.uuid4().hex
            job = {
                "scan_id": job_id,
                "kind": kind,
                "status": "queued",
                "phase": "Preparando análisis",
                "created_at": time.time(),
                "started_at": None,
                "finished_at": None,
                "files_processed": 0,
                "directories_processed": 0,
                "bytes_observed": 0,
                "error_count": 0,
                "result": None,
                "error": None,
                "options": options,
                "_cancel": threading.Event(),
            }
            self._jobs[job_id] = job
            thread = threading.Thread(target=self._run, args=(job_id,), daemon=True, name=f"nexus-scan-{job_id[:8]}")
            job["_thread"] = thread
            thread.start()
            return self._public(job)

    def _progress(self, job_id, values):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job["status"] in TERMINAL:
                return
            job.update({
                "files_processed": int(values.get("files", job["files_processed"])),
                "directories_processed": int(values.get("directories", job["directories_processed"])),
                "bytes_observed": int(values.get("bytes", job["bytes_observed"])),
                "error_count": int(values.get("errors", job["error_count"])),
                "phase": "Analizando archivos y carpetas",
            })

    def _run(self, job_id):
        with self._lock:
            job = self._jobs[job_id]
            job["status"] = "cancelling" if job["_cancel"].is_set() else "running"
            job["started_at"] = time.time()
            kind = job["kind"]
            options = dict(job["options"])
            cancel_event = job["_cancel"]

        try:
            callback = lambda values: self._progress(job_id, values)
            if kind == "profile":
                result = scan_system(
                    max_depth=options.get("max_depth"),
                    progress_callback=callback,
                    cancel_event=cancel_event,
                )
            elif kind == "duplicates":
                result = scan_duplicates(
                    roots=[options["root"]],
                    category=options.get("file_category", "all"),
                    min_size_bytes=options.get("min_size_bytes", 1),
                    progress_callback=callback,
                    cancel_event=cancel_event,
                )
            else:
                result = scan_large_files(
                    root=options.get("root"),
                    min_size_bytes=options.get("min_size_bytes", 1024 ** 3),
                    limit=options.get("limit", 100),
                    max_depth=options.get("max_depth"),
                    progress_callback=callback,
                    cancel_event=cancel_event,
                )
            coverage = result.get("coverage", {})
            with self._lock:
                job = self._jobs[job_id]
                job["result"] = result
                job["error_count"] = int(coverage.get("errors", len(result.get("errors", []))))
                if cancel_event.is_set() or coverage.get("cancelled") or result.get("cancelled"):
                    job["status"] = "cancelled"
                    job["phase"] = "Análisis cancelado; resultados parciales disponibles"
                elif result.get("error"):
                    job["status"] = "failed"
                    job["phase"] = "No se pudo completar el análisis"
                elif job["error_count"] or not coverage.get("complete", True):
                    job["status"] = "completed_with_warnings"
                    job["phase"] = "Análisis terminado con cobertura parcial"
                else:
                    job["status"] = "completed"
                    job["phase"] = "Análisis completado"
                job["finished_at"] = time.time()
        except Exception as exc:
            with self._lock:
                job = self._jobs[job_id]
                job["status"] = "failed"
                job["phase"] = "Error durante el análisis"
                job["error"] = str(exc)
                job["finished_at"] = time.time()

    def get(self, job_id):
        with self._lock:
            self._prune()
            job = self._jobs.get(job_id)
            return self._public(job) if job else None

    def cancel(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            if job["status"] in TERMINAL:
                return self._public(job)
            job["_cancel"].set()
            job["status"] = "cancelling"
            job["phase"] = "Solicitando cancelación"
            return self._public(job)

    @staticmethod
    def _public(job):
        if job is None:
            return None
        return {key: deepcopy(value) for key, value in job.items() if not key.startswith("_")}


scan_jobs = ScanJobManager()
