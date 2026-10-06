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
        status, result = self.call("DELETE", "/api/archives/archive-1")
        self.assertEqual(status, 200)
        self.assertTrue(result["deleted"])
        status, _ = self.call("GET", "/api/archives/archive-1")
        self.assertEqual(status, 404)

    def test_upload_rejects_unknown_format(self):
        status, result = self.call(
            "POST",
            "/api/imports",
            raw=b"invalid",
            headers={"HTTP_X_FILENAME": "plan.exe"},
        )
        self.assertEqual(status, 400)
        self.assertIn("Format", result["error"])

    def test_png_and_jpeg_uploads_keep_the_native_image(self):
        samples = (
            ("plan.png", b"\x89PNG\r\n\x1a\n" + b"0" * 32, "image/png"),
            ("plan.jpg", b"\xff\xd8\xff" + b"0" * 32, "image/jpeg"),
        )
        for filename, content, media_type in samples:
            with self.subTest(filename=filename):
                status, result = self.call(
                    "POST",
                    "/api/imports",
                    raw=content,
                    headers={"HTTP_X_FILENAME": filename},
                )
                self.assertEqual(status, 201)
                self.assertEqual(result["previewType"], media_type)
                self.assertEqual(result["conversion"], "Image native optimisée")
                self.assertTrue(result["originalUrl"].endswith("/original"))

        status, listing = self.call("GET", "/api/imports")
        self.assertEqual(status, 200)
        names = {plan["name"] for plan in listing["plans"]}
        self.assertTrue({"plan.png", "plan.jpg"}.issubset(names))

    def test_imported_plan_can_be_deleted(self):
        status, plan = self.call(
            "POST", "/api/imports", raw=b"\x89PNG\r\n\x1a\n" + b"0" * 32,
            headers={"HTTP_X_FILENAME": "a-supprimer.png"},
        )
        self.assertEqual(status, 201)
        status, result = self.call("DELETE", f"/api/imports/{plan['id']}")
        self.assertEqual(status, 200)
        self.assertTrue(result["deleted"])
        status, _ = self.call("GET", f"/api/imports/{plan['id']}/preview")
        self.assertEqual(status, 404)

    def test_pdf_is_kept_native_and_supports_byte_ranges(self):
        content = b"%PDF-1.7\n" + b"0" * 128
        with mock.patch("backend.importer._convert_pdf_to_svg", return_value=False):
            status, result = self.call(
                "POST",
                "/api/imports",
                raw=content,
                headers={"HTTP_X_FILENAME": "grand-plan.pdf"},
            )
        self.assertEqual(status, 201)
        self.assertEqual(result["previewType"], "application/pdf")
        self.assertEqual(result["conversion"], "PDF natif optimisé")
        status, preview = self.call(
            "GET",
            f"/api/imports/{result['id']}/preview",
            headers={"HTTP_RANGE": "bytes=0-7"},
        )
        self.assertEqual(status, 206)
        self.assertEqual(preview, b"%PDF-1.7")

    def test_dwg_and_dxf_uploads_are_rejected(self):
        for filename in ("plan.dwg", "plan.dxf"):
            with self.subTest(filename=filename):
                status, result = self.call(
                    "POST",
                    "/api/imports",
                    raw=b"unsupported-cad-content",
                    headers={"HTTP_X_FILENAME": filename},
                )
                self.assertEqual(status, 400)
                self.assertIn("Format", result["error"])

    def test_renamed_non_pdf_file_is_rejected(self):
        status, result = self.call(
            "POST",
            "/api/imports",
            raw=b"not-really-a-pdf",
            headers={"HTTP_X_FILENAME": "faux-plan.pdf"},
        )
        self.assertEqual(status, 400)
        self.assertIn("correspond pas", result["error"])

    def test_vector_pdf_is_converted_to_svg(self):
        from backend import importer

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.pdf"
            output = Path(directory) / "preview.svg"
            source.write_bytes(b"%PDF-1.7\n")

            def write_vector_svg(*_args, **_kwargs):
                output.write_text("<svg width='842' height='595'>" + "<path d='M0 0L1 1'/>" * 20 + "</svg>", encoding="utf-8")

            with mock.patch("backend.importer.shutil.which", return_value="pdftocairo"), mock.patch("backend.importer.subprocess.run", side_effect=write_vector_svg):
                self.assertTrue(importer._convert_pdf_to_svg(source, output))

    def test_empty_svg_falls_back_to_the_original_pdf(self):
        from backend import importer

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.pdf"
            output = Path(directory) / "preview.svg"
            source.write_bytes(b"%PDF-1.7\n")

            def write_empty_svg(*_args, **_kwargs):
                output.write_text("<svg width='0' height='0'><path d='M0 0'/></svg>", encoding="utf-8")

            with mock.patch("backend.importer.shutil.which", return_value="pdftocairo"), mock.patch("backend.importer.subprocess.run", side_effect=write_empty_svg):
                self.assertFalse(importer._convert_pdf_to_svg(source, output))
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
