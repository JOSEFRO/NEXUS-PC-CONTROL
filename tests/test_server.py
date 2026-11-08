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

    def test_unknown_background_scan_returns_404(self):
        response = self.client.get("/api/storage/scans/not-a-real-job")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
