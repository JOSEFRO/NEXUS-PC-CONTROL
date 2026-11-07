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

    def test_unknown_background_scan_returns_404(self):
        response = self.client.get("/api/storage/scans/not-a-real-job")
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
