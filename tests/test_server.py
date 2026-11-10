import unittest

from app.server import app


class LocalDashboardTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"NEXUS PC CONTROL", response.data)

    def test_security_headers_are_present(self):
        response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_untrusted_host_is_rejected(self):
        response = self.client.get("/", headers={"Host": "untrusted.example"})
        self.assertEqual(response.status_code, 403)

    def test_invalid_cleanup_payload_is_rejected(self):
        response = self.client.post("/api/cleanup", json={"ids": "user_temp"})
        self.assertEqual(response.status_code, 400)

    def test_unknown_cleanup_category_is_not_accepted(self):
        response = self.client.post("/api/cleanup", json={"ids": ["not-allowed"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["results"][0]["status"], "rechazado")



    def test_background_scan_rejects_invalid_kind(self):
        response = self.client.post("/api/storage/scans", json={"kind": "unknown"})
        self.assertEqual(response.status_code, 400)

    def test_background_scan_returns_job_identifier(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "sample.bin").write_bytes(b"nexus")
            response = self.client.post("/api/storage/scans", json={
                "kind": "large_files", "root": directory, "min_size_mb": 1
            })
            self.assertEqual(response.status_code, 202)
            payload = response.get_json()
            self.assertTrue(payload["scan_id"])
            status = self.client.get("/api/storage/scans/" + payload["scan_id"])
            self.assertEqual(status.status_code, 200)
            self.assertIn(status.get_json()["status"], {
                "queued", "running", "completed", "completed_with_warnings"
            })

    def test_storage_categories_endpoint_returns_list(self):
        response = self.client.get("/api/storage/categories")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json()["categories"], list)

    def test_storage_browse_rejects_unknown_category(self):
        response = self.client.get("/api/storage/browse/not-allowed")
        self.assertEqual(response.status_code, 400)

    def test_storage_delete_rejects_protected_category(self):
        response = self.client.post("/api/storage/delete", json={
            "category": "appdata_local", "paths": ["sample.txt"]
        })
        self.assertEqual(response.status_code, 400)

    def test_storage_delete_rejects_invalid_payload(self):
        response = self.client.post("/api/storage/delete", json={
            "category": "downloads", "paths": "../outside.txt"
        })
        self.assertEqual(response.status_code, 400)

    def test_storage_delete_rejects_non_string_category(self):
        response = self.client.post("/api/storage/delete", json={
            "category": {"unexpected": "object"}, "paths": ["file.txt"]
        })
        self.assertEqual(response.status_code, 400)

    def test_storage_delete_rejects_symlinked_parent(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from app import scanner

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Downloads"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            protected = outside / "keep.txt"
            protected.write_text("keep")
            try:
                (root / "shortcut").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("El entorno no permite crear enlaces simbólicos.")
            with patch.object(scanner, "storage_categories", return_value=[
                {"id": "downloads", "name": "Descargas", "path": str(root), "deletable": True}
            ]):
                result = scanner.delete_storage_files("downloads", ["shortcut/keep.txt"])
            self.assertEqual(result["deleted"], 0)
            self.assertTrue(protected.exists())

    def test_storage_delete_removes_only_regular_file(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from app import scanner

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "Downloads"
            root.mkdir()
            target = root / "sample.txt"
            target.write_text("nexus")
            with patch.object(scanner, "storage_categories", return_value=[
                {"id": "downloads", "name": "Descargas", "path": str(root), "deletable": True}
            ]):
                result = scanner.delete_storage_files("downloads", ["sample.txt"])
            self.assertEqual(result["deleted"], 1)
            self.assertFalse(target.exists())


    def test_settings_api_returns_defaults_and_accepts_safe_patch(self):
        from unittest.mock import patch
        from app import preferences
        with patch.object(preferences, "settings_path") as path:
            import tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as directory:
                path.return_value = Path(directory) / "settings.json"
                response = self.client.get("/api/settings")
                self.assertEqual(response.status_code, 200)
                updated = self.client.put("/api/settings", json={
                    "appearance": {"theme": "light"},
                    "modules": {"duplicates": False},
                    "unknown": {"unsafe": True},
                })
                self.assertEqual(updated.status_code, 200)
                self.assertEqual(updated.get_json()["appearance"]["theme"], "light")
                self.assertFalse(updated.get_json()["modules"]["duplicates"])
                self.assertNotIn("unknown", updated.get_json())

    def test_duplicate_scan_rejects_protected_or_unknown_category(self):
        response = self.client.post("/api/storage/duplicates", json={"category": "appdata_local"})
        self.assertEqual(response.status_code, 400)

    def test_duplicate_scan_starts_background_job(self):
        from unittest.mock import patch
        with patch("app.server.storage_categories", return_value=[
            {"id": "downloads", "name": "Descargas", "path": "/tmp", "deletable": True}
        ]):
            response = self.client.post("/api/storage/duplicates", json={
                "category": "downloads", "file_category": "images"
            })
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["kind"], "duplicates")

    def test_unknown_background_scan_returns_404(self):
        response = self.client.get("/api/storage/scans/not-a-real-job")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
