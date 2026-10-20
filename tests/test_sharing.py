import importlib
import io
import json
import os
import pathlib
import tempfile
import time
import unittest
import uuid
from unittest import mock


SVG = '<svg xmlns="http://www.w3.org/2000/svg"><g><circle cx="10" cy="10" r="5" fill="#287dc0"/></g></svg>'


class SharingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = mock.patch.dict(os.environ, {
            "ARCENAL_DB_PATH": self.directory.name + "/database.sqlite3",
            "ARCENAL_UPLOAD_DIR": self.directory.name + "/uploads",
            "ARCENAL_ALLOW_ANONYMOUS": "0",
        })
        self.environment.start()
        self.app = importlib.import_module("backend.app")
        self.db = importlib.import_module("backend.db")
        self.sharing = importlib.import_module("backend.sharing")
        self.importer = importlib.import_module("backend.importer")
        self.old_paths = self.db.DB_PATH, self.importer.UPLOAD_DIR
        self.db.DB_PATH = self.directory.name + "/database.sqlite3"
        self.importer.UPLOAD_DIR = pathlib.Path(self.directory.name) / "uploads"
        self.db.initialize(); self.sharing.initialize()
        self.address = uuid.uuid4().hex
        _, plan, _ = self.call("POST", "/api/imports", raw=b"\x89PNG\r\n\x1a\nplan", headers={"HTTP_X_FILENAME": "plan.png"})
        self.plan_id = plan["id"]
        self.state = {"name": "Client Atelier", "location": "Atelier", "client": "Client", "planDate": "2026-10-20", "planFile": {"id": self.plan_id}, "calibration": {"metersPerNativeUnit": 2}, "interventions": [{"id": "team1", "company": "Société 1", "color": "#287dc0", "activity": 40, "unit": "Ci", "isotope": "Ir-192"}], "circles": [{"id": "point1", "interventionId": "team1", "cx": 10, "cy": 10, "radius": 5, "threshold": 2.5}], "author": {"name": "Auteur", "role": "CRP"}}
        self.call("PUT", "/api/projects/project1", self.state)

    def tearDown(self):
        self.db.DB_PATH, self.importer.UPLOAD_DIR = self.old_paths
        self.environment.stop()
        self.directory.cleanup()

    def call(self, method, path, payload=None, headers=None, raw=None, user="alice", cookie=""):
        body = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else b"")
        env = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body), "REMOTE_ADDR": self.address, "HTTP_COOKIE": cookie, "HTTP_X_CROBARD_BASE": "/arcenal-draw/consultation/"}
        if user:
            env["HTTP_REMOTE_USER"] = user
        env.update(headers or {})
        captured = {}
        def respond(status, fields):
            captured.update(status=int(status.split()[0]), headers=dict(fields))
        data = b"".join(self.app.application(env, respond))
        try:
            data = json.loads(data)
        except (ValueError, UnicodeDecodeError):
            pass
        return captured["status"], data, captured["headers"]

    def publish(self, **changes):
        payload = {"overlaySvg": SVG, **changes}
        return self.call("POST", "/api/projects/project1/consultation", payload, {"HTTP_X_CROBARD_PUBLISH": "1"})

    def open(self, share, code=None):
        status, _, headers = self.call("POST", f'/public/{share["id"]}/unlock', {"code": code or share["accessCode"]}, {"HTTP_X_CROBARD_VIEW": "1"}, user=None)
        return status, headers.get("Set-Cookie", "").split(";")[0], headers

    def test_snapshot_is_protected_and_minimizes_private_data(self):
        status, result, _ = self.publish()
        self.assertEqual(status, 200)
        share = result["share"]
        status, _, _ = self.call("GET", f'/public/{share["id"]}/state', user=None)
        self.assertEqual(status, 401)
        status, cookie, headers = self.open(share)
        self.assertEqual(status, 200)
        self.assertIn("Secure; HttpOnly; SameSite=Strict", headers["Set-Cookie"])
        self.assertIn(f'Path=/arcenal-draw/consultation/api/{share["id"]}/', headers["Set-Cookie"])
        status, model, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertNotIn("owner", model); self.assertNotIn("planFile", model); self.assertNotIn("projectId", model)
        status, contents, headers = self.call("GET", f'/public/{share["id"]}/snapshot/{model["revision"]}/plan', user=None, cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertTrue(contents.startswith(b"\x89PNG"))
        with self.db.connection() as database:
            stored = database.execute("SELECT code_hash FROM client_shares").fetchone()[0]
            token = database.execute("SELECT token_hash FROM client_sessions").fetchone()[0]
        self.assertNotEqual(stored, share["accessCode"])
        self.assertNotEqual(token, cookie.split("=", 1)[1])

    def test_republication_preserves_link_and_old_page_snapshot(self):
        _, data, _ = self.publish()
        share = data["share"]
        _, cookie, _ = self.open(share)
        _, first, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.state["location"] = "Modification non publiée"
        self.call("PUT", "/api/projects/project1", self.state)
        _, unchanged, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.assertEqual(unchanged["location"], first["location"])
        _, second_share, _ = self.publish()
        self.assertEqual(second_share["share"]["id"], share["id"])
        self.assertNotIn("accessCode", second_share["share"])
        _, second, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.assertEqual(second["location"], "Modification non publiée")
        self.assertNotEqual(first["revision"], second["revision"])
        status, _, _ = self.call("GET", f'/public/{share["id"]}/snapshot/{first["revision"]}/plan', user=None, cookie=cookie)
        self.assertEqual(status, 200)

    def test_revocation_expiry_and_code_change_block_existing_sessions(self):
        _, data, _ = self.publish(accessCode="code-initial-test")
        share = data["share"]
        _, cookie, _ = self.open(share)
        self.publish(accessCode="nouveau-code-test")
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)[0], 401)
        self.assertEqual(self.open(share)[0], 401)
        _, new_cookie, _ = self.open(share, "nouveau-code-test")
        with self.db.connection() as database:
            database.execute("UPDATE client_shares SET expires_at=?", (time.time() - 1,))
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/status', user=None, cookie=new_cookie)[0], 401)
        self.publish()
        _, new_cookie, _ = self.open(share, "nouveau-code-test")
        self.call("DELETE", "/api/projects/project1/consultation", headers={"HTTP_X_CROBARD_PUBLISH": "1"})
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=new_cookie)[0], 401)
        self.assertEqual(self.open(share, "nouveau-code-test")[0], 401)

    def test_other_user_cannot_manage_share_or_publish_foreign_plan(self):
        self.publish()
        for method in ["GET", "POST", "DELETE"]:
            self.assertEqual(self.call(method, "/api/projects/project1/consultation", {"overlaySvg": SVG}, {"HTTP_X_CROBARD_PUBLISH": "1"}, user="bob")[0], 404)
        self.call("PUT", "/api/projects/bob-project", self.state, user="bob")
        self.assertEqual(self.call("POST", "/api/projects/bob-project/consultation", {"overlaySvg": SVG}, {"HTTP_X_CROBARD_PUBLISH": "1"}, user="bob")[0], 400)

    def test_public_session_cannot_edit_or_read_private_routes(self):
        _, result, _ = self.publish()
        share = result["share"]
        _, cookie, _ = self.open(share)
        for method, path in [("PUT", "/api/projects/project1"), ("GET", "/api/projects"), ("DELETE", f'/api/imports/{self.plan_id}')]:
            self.assertEqual(self.call(method, path, {}, user=None, cookie=cookie)[0], 401)
        for method in ["POST", "PUT", "DELETE"]:
            self.assertEqual(self.call(method, f'/public/{share["id"]}/state', {}, user=None, cookie=cookie)[0], 405)

    def test_public_session_cannot_read_another_share_revision(self):
        _, one, _ = self.publish()
        _, cookie, _ = self.open(one["share"])
        self.call("PUT", "/api/projects/project2", self.state)
        _, two, _ = self.call("POST", "/api/projects/project2/consultation", {"overlaySvg": SVG}, {"HTTP_X_CROBARD_PUBLISH": "1"})
        self.assertEqual(self.call("GET", f'/public/{two["share"]["id"]}/state', user=None, cookie=cookie)[0], 401)
        _, second_cookie, _ = self.open(two["share"])
        _, second_state, _ = self.call("GET", f'/public/{two["share"]["id"]}/state', user=None, cookie=second_cookie)
        self.assertEqual(self.call("GET", f'/public/{one["share"]["id"]}/snapshot/{second_state["revision"]}/plan', user=None, cookie=cookie)[0], 404)

    def test_wrong_codes_are_throttled_and_csrf_headers_required(self):
        _, result, _ = self.publish()
        share = result["share"]
        for _ in range(8):
            self.assertEqual(self.open(share, "wrong-code-test")[0], 401)
        self.assertEqual(self.open(share)[0], 429)
        self.assertEqual(self.call("POST", f'/public/{share["id"]}/unlock', {"code": share["accessCode"]}, user=None)[0], 403)
        self.assertEqual(self.call("POST", "/api/projects/project1/consultation", {"overlaySvg": SVG})[0], 403)

    def test_svg_rejects_scripts_external_images_and_nonfinite_geometry(self):
        for payload in [
            SVG.replace('<g>', '<g onclick="alert(1)">'),
            SVG.replace('<g>', '<script>alert(1)</script><g>'),
            SVG.replace('<g>', '<image href="https://external.example/image.png"/><g>'),
            SVG.replace('<g>', '<foreignObject/><g>'),
            SVG.replace('<g>', '<g id="access-form">'),
            '<!DOCTYPE svg [<!ENTITY attack "data">]>' + SVG,
            SVG.replace('cx="10"', 'cx="NaN"'),
        ]:
            self.assertEqual(self.publish(overlaySvg=payload)[0], 400)
        self.assertEqual(self.publish(accessCode="court")[0], 400)
        self.assertEqual(self.publish(expiresOn="2001-01-01")[0], 400)

    def test_snapshot_payload_is_frozen_and_uses_owned_plan(self):
        snapshot = {**self.state, "location": "Copie explicite"}
        _, result, _ = self.publish(snapshot=snapshot)
        share = result["share"]
        _, cookie, _ = self.open(share)
        _, model, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.assertEqual(model["location"], "Copie explicite")
        self.assertEqual(self.publish(snapshot={**snapshot, "planFile": {"id": "a" * 32}})[0], 400)
        self.assertEqual(self.publish(snapshot={**snapshot, "calibration": None})[0], 400)

    def test_expired_session_and_invalid_revision_are_refused(self):
        _, result, _ = self.publish()
        share = result["share"]
        _, cookie, _ = self.open(share)
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/snapshot/{"0" * 32}/plan', user=None, cookie=cookie)[0], 404)
        with self.db.connection() as database:
            database.execute("UPDATE client_sessions SET expires_at=?", (time.time() - 1,))
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)[0], 401)

    def test_access_code_is_not_returned_by_management_reads(self):
        _, first, _ = self.publish()
        self.assertIn("accessCode", first["share"])
        _, second, _ = self.call("GET", "/api/projects/project1/consultation")
        self.assertNotIn("accessCode", second["share"])
        self.assertNotIn("code_hash", second["share"])
        self.assertNotIn("salt", second["share"])

    def test_snapshot_survives_source_deletion_and_logout_ends_access(self):
        _, result, _ = self.publish()
        share = result["share"]
        _, cookie, _ = self.open(share)
        _, state, _ = self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)
        self.call("DELETE", f'/api/imports/{self.plan_id}')
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/snapshot/{state["revision"]}/plan', user=None, cookie=cookie)[0], 200)
        self.assertEqual(self.call("POST", f'/public/{share["id"]}/logout', headers={"HTTP_X_CROBARD_VIEW": "1"}, user=None, cookie=cookie)[0], 200)
        self.assertEqual(self.call("GET", f'/public/{share["id"]}/state', user=None, cookie=cookie)[0], 401)
