import tempfile
import unittest
from pathlib import Path

from app.duplicates import scan_duplicates


class DuplicateScannerTests(unittest.TestCase):
    def test_finds_identical_content_with_different_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.jpg").write_bytes(b"same-image-data")
            (root / "copy.jpg").write_bytes(b"same-image-data")
            result = scan_duplicates([root], category="images")
            self.assertEqual(result["duplicate_groups"], 1)
            self.assertEqual(result["duplicate_files"], 2)
            self.assertEqual(result["potential_waste_bytes"], len(b"same-image-data"))

    def test_same_size_different_content_is_not_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.jpg").write_bytes(b"image-A")
            (root / "two.jpg").write_bytes(b"image-B")
            result = scan_duplicates([root], category="images")
            self.assertEqual(result["duplicate_groups"], 0)

    def test_category_filter_ignores_non_matching_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.jpg").write_bytes(b"same")
            (root / "two.txt").write_bytes(b"same")
            result = scan_duplicates([root], category="images")
            self.assertEqual(result["duplicate_groups"], 0)
            self.assertEqual(result["files_scanned"], 1)

    def test_rejects_symlink_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "target"
            target.mkdir()
            link = base / "link"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest("El entorno no permite crear enlaces simbólicos.")
            result = scan_duplicates([link])
            self.assertEqual(result["files_scanned"], 0)
            self.assertTrue(result["errors"])

    def test_invalid_category_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                scan_duplicates([directory], category="executables")


if __name__ == "__main__":
    unittest.main()
