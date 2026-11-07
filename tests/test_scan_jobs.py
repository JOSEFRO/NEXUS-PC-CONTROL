import tempfile
import threading
import time
import unittest
from pathlib import Path

from app.scan_jobs import ScanJobManager
from app.scanner import scan_large_files


class ScanJobTests(unittest.TestCase):
    def test_background_job_reports_terminal_result_and_counters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.bin").write_bytes(b"x" * 128)
            manager = ScanJobManager()
            job = manager.start("large_files", {
                "root": str(root), "min_size_bytes": 1, "limit": 10
            })
            deadline = time.time() + 5
            snapshot = manager.get(job["scan_id"])
            while snapshot["status"] not in {
                "cancelled", "completed", "completed_with_warnings", "failed"
            } and time.time() < deadline:
                time.sleep(0.02)
                snapshot = manager.get(job["scan_id"])

            self.assertEqual(snapshot["status"], "completed")
            self.assertEqual(snapshot["result"]["files"][0]["name"], "sample.bin")
            self.assertGreaterEqual(snapshot["files_processed"], 1)
            self.assertGreaterEqual(snapshot["directories_processed"], 1)

    def test_cancelled_scanner_returns_partial_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.bin").write_bytes(b"x" * 128)
            cancel = threading.Event()
            cancel.set()
            result = scan_large_files(root=root, min_size_bytes=1, cancel_event=cancel)

            self.assertTrue(result["coverage"]["cancelled"])
            self.assertFalse(result["coverage"]["complete"])

    def test_progress_callback_receives_real_counters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.bin").write_bytes(b"a" * 32)
            (root / "b.bin").write_bytes(b"b" * 64)
            updates = []
            scan_large_files(root=root, min_size_bytes=1, progress_callback=updates.append)

            self.assertTrue(updates)
            self.assertEqual(updates[-1]["files"], 2)
            self.assertEqual(updates[-1]["bytes"], 96)


if __name__ == "__main__":
    unittest.main()
