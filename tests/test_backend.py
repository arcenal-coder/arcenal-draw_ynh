import importlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

class BackendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["ARCENAL_DB_PATH"] = os.path.join(cls.temp_dir.name, "arcenal.sqlite3")
        os.environ["ARCENAL_UPLOAD_DIR"] = os.path.join(cls.temp_dir.name, "uploads")
        os.environ["ARCENAL_ALLOW_ANONYMOUS"] = "1"
        cls.application = staticmethod(importlib.import_module("backend.app").application)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def call(self, method, path, payload=None, headers=None, raw=None):
        body = raw if raw is not None else (b"" if payload is None else json.dumps(payload).encode("utf-8"))
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "wsgi.input": io.BytesIO(body),
            "CONTENT_LENGTH": str(len(body)),
        }
        environ.update(headers or {})
        captured = {}

        def start_response(status, response_headers):
            captured["status"] = status
            captured["headers"] = dict(response_headers)

        response_body = b"".join(self.application(environ, start_response))
        try:
            payload = json.loads(response_body or b"null")
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = response_body
        return int(captured["status"].split()[0]), payload

    def test_project_archive_and_listing(self):
        state = {"name": "Plan test", "location": "Atelier", "circles": [], "interventions": []}
        status, _ = self.call("PUT", "/api/projects/project-1", state)
        self.assertEqual(status, 200)
        status, project = self.call("GET", "/api/projects/project-1")
        self.assertEqual(status, 200)
        self.assertEqual(project["state"]["location"], "Atelier")
        status, listing = self.call("GET", "/api/projects")
        self.assertEqual(status, 200)
        self.assertEqual(len(listing["projects"]), 1)
        status, _ = self.call("POST", "/api/archives", {"id": "archive-1", "projectId": "project-1", "exportName": "plan.pdf", "state": state})
        self.assertEqual(status, 201)
        status, archive = self.call("GET", "/api/archives/archive-1")
        self.assertEqual(status, 200)
        self.assertEqual(archive["state"]["name"], "Plan test")

    def test_upload_rejects_unknown_format(self):
        status, result = self.call(
            "POST",
            "/api/imports",
            raw=b"invalid",
            headers={"HTTP_X_FILENAME": "plan.exe"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Format", result["error"])

    def test_image_upload_produces_a_readable_preview(self):
        status, result = self.call(
            "POST",
            "/api/imports",
            raw=b"opaque-image-content",
            headers={"HTTP_X_FILENAME": "plan.png"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(result["status"], "converted")
        status, _ = self.call("GET", f"/api/imports/{result['id']}/preview")
        self.assertEqual(status, 200)

    def test_pdf_is_kept_native_and_supports_byte_ranges(self):
        content = b"%PDF-1.7\n" + b"0" * 128
        status, result = self.call(
            "POST",
            "/api/imports",
            raw=content,
            headers={"HTTP_X_FILENAME": "grand-plan.pdf"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(result["previewType"], "application/pdf")
        self.assertEqual(result["conversion"], "PDF natif")
        status, preview = self.call(
            "GET",
            f"/api/imports/{result['id']}/preview",
            headers={"HTTP_RANGE": "bytes=0-7"},
        )
        self.assertEqual(status, 206)
        self.assertEqual(preview, b"%PDF-1.7")

    def test_dwg_warnings_are_accepted_when_a_dxf_is_produced(self):
        from backend import importer

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plan.dwg"
            output = Path(directory) / "plan.dxf"
            source.write_bytes(b"DWG")

            def produce_dxf(*_args, **_kwargs):
                output.write_text("0\nSECTION\n0\nEOF\n", encoding="ascii")
                return mock.Mock(returncode=1, stderr="Warning: Unstable Class MATERIAL", stdout="")

            with mock.patch("backend.importer.subprocess.run", side_effect=produce_dxf):
                self.assertTrue(importer._convert_dwg("dwg2dxf", source, output))

    def test_dwg_failure_remains_blocking_without_output(self):
        from backend import importer

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "plan.dwg"
            output = Path(directory) / "plan.dxf"
            source.write_bytes(b"DWG")
            result = mock.Mock(returncode=1, stderr="READ ERROR", stdout="")

            with mock.patch("backend.importer.subprocess.run", return_value=result):
                with self.assertRaises(importer.ImportErrorSafe):
                    importer._convert_dwg("dwg2dxf", source, output)


if __name__ == "__main__":
    unittest.main()
