import tempfile
import unittest
from pathlib import Path

from app.scanner import GIB, folder_size, get_overview, scan_large_files


class StorageScannerTests(unittest.TestCase):
    def test_folder_size_scans_beyond_four_levels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deep = root / "one" / "two" / "three" / "four" / "five" / "six"
            deep.mkdir(parents=True)
            payload = deep / "payload.bin"
            payload.write_bytes(b"x" * 257)

            self.assertEqual(folder_size(root), 257)

    def test_folder_size_includes_development_folders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependency = root / "node_modules" / "package"
            dependency.mkdir(parents=True)
            (dependency / "bundle.js").write_bytes(b"n" * 83)

            self.assertEqual(folder_size(root), 83)

    def test_large_file_threshold_is_configurable_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            small = root / "small.dat"
            large = root / "large.dat"
            small.write_bytes(b"a" * 10)
            large.write_bytes(b"b" * 100)

            result = scan_large_files(root=root, min_size_bytes=50, limit=10)

            self.assertEqual([item["name"] for item in result["files"]], ["large.dat"])
            self.assertEqual(small.stat().st_size, 10)
            self.assertEqual(large.stat().st_size, 100)
            self.assertTrue(result["coverage"]["complete"])

    def test_large_file_results_are_sorted_and_limited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.bin").write_bytes(b"a" * 60)
            (root / "b.bin").write_bytes(b"b" * 90)
            (root / "c.bin").write_bytes(b"c" * 120)

            result = scan_large_files(root=root, min_size_bytes=1, limit=2)

            self.assertEqual([item["name"] for item in result["files"]], ["c.bin", "b.bin"])
            self.assertEqual(result["coverage"]["matched"], 3)
            self.assertEqual(result["coverage"]["returned"], 2)

    def test_missing_scan_root_is_reported(self):
        result = scan_large_files(root=Path(tempfile.gettempdir()) / "nexus-path-that-does-not-exist")

        self.assertIn("error", result)
        self.assertFalse(result["coverage"]["complete"])

    def test_overview_reports_capacity_fields(self):
        result = get_overview()

        self.assertIn("drives", result)
        self.assertIn("complete", result)
        for drive in result["drives"]:
            self.assertIn("total_bytes", drive)
            self.assertIn("free_bytes", drive)
            self.assertIn("is_system", drive)


if __name__ == "__main__":
    unittest.main()
