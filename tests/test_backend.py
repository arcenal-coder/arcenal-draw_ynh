import importlib
import io
import json
import os
import tempfile
import unittest


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
        return int(captured["status"].split()[0]), json.loads(response_body or b"null")

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


if __name__ == "__main__":
    unittest.main()
