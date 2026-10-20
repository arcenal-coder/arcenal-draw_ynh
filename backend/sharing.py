"""Published client views: isolated snapshots and revocable read-only sessions."""
import base64
import hashlib
import hmac
import json
import math
import errno
import os
import pathlib
import re
import secrets
import shutil
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import date, datetime, time as daytime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie

from backend import db
from backend.importer import preview_file

SESSION_SECONDS = 8 * 3600
ASSETS = {"onyx-logo.png", "symbole-radioactif.png", "gyrophare-orange.png", "barriere-chantier.png", "cone-signalisation.png", "panneau-interdiction.png"}
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def root_dir():
    return pathlib.Path(db.DB_PATH).parent / "consultations"


def initialize():
    with db.connection() as database:
        database.executescript("""
            CREATE TABLE IF NOT EXISTS client_shares (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, project_id TEXT NOT NULL,
                salt TEXT NOT NULL, code_hash TEXT NOT NULL, enabled INTEGER NOT NULL,
                expires_at REAL, current_revision TEXT, UNIQUE(owner, project_id)
            );
            CREATE TABLE IF NOT EXISTS client_revisions (
                id TEXT PRIMARY KEY, share_id TEXT NOT NULL, metadata TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY(share_id) REFERENCES client_shares(id)
            );
            CREATE TABLE IF NOT EXISTS client_sessions (
                token_hash TEXT PRIMARY KEY, share_id TEXT NOT NULL, expires_at REAL NOT NULL,
                FOREIGN KEY(share_id) REFERENCES client_shares(id)
            );
            CREATE TABLE IF NOT EXISTS client_attempts (
                key TEXT PRIMARY KEY, window_start REAL NOT NULL, count INTEGER NOT NULL
            );
        """)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def code_digest(code, salt):
    # OWASP's 16 MiB scrypt profile avoids adding a password library.
    return hashlib.scrypt(code.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=5).hex()


def image_url(value):
    if value in {"assets/" + name for name in ASSETS}:
        return value
    if not isinstance(value, str) or len(value) > 3_000_000:
        raise ValueError("Image de publication invalide ou trop volumineuse.")
    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)", value)
    if not match:
        raise ValueError("Seules les images PNG ou JPEG intégrées sont autorisées.")
    try:
        data = base64.b64decode(match[2], validate=True)
    except ValueError as error:
        raise ValueError("Image intégrée invalide.") from error
    signature = b"\x89PNG\r\n\x1a\n" if match[1] == "png" else b"\xff\xd8\xff"
    if len(data) > 2_000_000 or not data.startswith(signature):
        raise ValueError("Image intégrée invalide ou supérieure à 2 Mo.")
    return value


def sanitize_svg(markup):
    if not isinstance(markup, str) or len(markup.encode()) > 4_000_000 or re.search(r"<!", markup):
        raise ValueError("Annotations invalides ou trop volumineuses.")
    try:
        source = ET.fromstring(markup)
    except ET.ParseError as error:
        raise ValueError("Annotations SVG invalides.") from error
    tags = {"svg", "g", "path", "rect", "circle", "line", "image", "text", "tspan", "defs", "clipPath"}
    numbers = {"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "stroke-width", "fill-opacity", "opacity", "font-size", "data-x", "data-y"}
    count = 0

    def clean(node, depth=0):
        nonlocal count
        count += 1
        tag = node.tag.removeprefix("{" + SVG_NS + "}")
        if tag not in tags or depth > 20 or count > 20000:
            raise ValueError("Contenu SVG non autorisé.")
        result = ET.Element("{" + SVG_NS + "}" + tag)
        for key, value in node.attrib.items():
            if key == "{http://www.w3.org/1999/xlink}href":
                key = "href"
            if key in numbers:
                number = float(value)
                if not math.isfinite(number) or abs(number) > 10_000_000:
                    raise ValueError("Coordonnée SVG invalide.")
            elif key in {"fill", "stroke"}:
                if not re.fullmatch(r"#[0-9a-fA-F]{3,8}|(?:rgb|rgba)\([0-9.,% /]+\)|none|black|white|transparent|currentColor", value):
                    raise ValueError("Couleur SVG invalide.")
            elif key == "d":
                if len(value) > 1_000_000 or not re.fullmatch(r"[MmZzLlHhVvCcSsQqTtAa0-9eE+.,\s-]*", value):
                    raise ValueError("Tracé SVG invalide.")
            elif key == "transform":
                if not re.fullmatch(r"(?:(?:translate|scale|rotate|matrix|skewX|skewY)\([0-9eE+.,\s-]+\)\s*)+", value):
                    raise ValueError("Transformation SVG invalide.")
            elif key == "href" and tag == "image":
                value = image_url(value)
            elif key == "clip-path":
                if value != "url(#impact-image-clip)":
                    raise ValueError("Découpe SVG invalide.")
            elif key == "id":
                if value != "impact-image-clip":
                    raise ValueError("Identifiant SVG invalide.")
            elif key == "viewBox":
                if not re.fullmatch(r"[0-9eE+.,\s-]+", value):
                    raise ValueError("Dimensions SVG invalides.")
            elif key == "stroke-dasharray":
                if value != "none" and not re.fullmatch(r"[0-9.,\s]+", value):
                    raise ValueError("Style de trait invalide.")
            elif key == "data-fixed" and value == "1":
                pass
            elif key in {"text-anchor", "font-weight", "font-family", "preserveAspectRatio", "vector-effect", "dominant-baseline"}:
                if not re.fullmatch(r"[a-zA-Z0-9 ,.'_-]{0,120}", value):
                    raise ValueError("Style SVG invalide.")
            else:
                raise ValueError("Attribut SVG non autorisé.")
            result.set(key, value)
        result.text = node.text
        result.tail = node.tail
        for child in node:
            result.append(clean(child, depth + 1))
        return result

    if source.tag != "{" + SVG_NS + "}svg":
        raise ValueError("Racine SVG invalide.")
    return ET.tostring(clean(source), encoding="unicode")


def finite(value, minimum=-10_000_000, maximum=10_000_000):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("Données géométriques invalides.")
    return value


def public_metadata(state, overlay):
    if not isinstance(state.get("calibration"), dict) or not isinstance(state.get("circles", []), list) or not isinstance(state.get("interventions", []), list):
        raise ValueError("Projet incomplet pour la publication.")
    factor = finite(state.get("calibration", {}).get("metersPerNativeUnit"), 1e-12, 1e9)
    text = lambda value, limit=300: str(value or "")[:limit]
    teams = []
    circles = state.get("circles", [])
    if not all(isinstance(item, dict) for item in circles + state.get("interventions", [])):
        raise ValueError("Annotations du projet invalides.")
    if len(circles) > 5000 or len(state.get("interventions", [])) > 10:
        raise ValueError("Projet trop volumineux pour cette publication.")
    for item in state.get("interventions", []):
        last = next((c for c in reversed(circles) if c.get("interventionId") == item.get("id")), {})
        teams.append({
            "id": text(item.get("id"), 80), "company": text(item.get("company")),
            "color": item.get("color") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(item.get("color"))) else "#287dc0",
            "isotope": text(item.get("isotope"), 20), "activity": text(item.get("activity"), 30), "unit": text(item.get("unit"), 10),
            "start": text(item.get("scheduleStart"), 5), "end": text(item.get("scheduleEnd"), 5),
            "attenuated": bool(last.get("attenuated", item.get("attenuation"))),
            "threshold": last.get("threshold", item.get("displayThreshold", 2.5)),
            "distance": finite(last["radius"], 0) if "radius" in last else None,
            "overDistance": finite(item.get("overDistance", 50), 0) if item.get("overEnabled") else None,
        })
    zones = [{"team": text(c.get("interventionId"), 80), "x": finite(c.get("cx")), "y": finite(c.get("cy")), "radius": finite(c.get("radius"), 0) / factor,
              "distance": c.get("radius"), "threshold": c.get("threshold", 2.5), "attenuated": bool(c.get("attenuated", True))} for c in circles]

    def person(value):
        value = value if isinstance(value, dict) else {}
        signature = value.get("signature") or {}
        if not isinstance(signature, dict):
            raise ValueError("Signature invalide.")
        data = signature.get("dataUrl")
        return {"name": text(value.get("name")), "role": text(value.get("role")), "signature": image_url(data) if data else None}

    logo_info = state.get("logo") or {}
    if not isinstance(logo_info, dict):
        raise ValueError("Logo invalide.")
    logo = logo_info.get("dataUrl")
    return {"name": text(state.get("name")), "date": text(state.get("planDate"), 10), "location": text(state.get("location")),
            "client": text(state.get("client")), "logo": image_url(logo) if logo else None,
            "author": person(state.get("author")), "validator": person(state.get("validator")) if state.get("validatorEnabled") else None,
            "width": 297 if state.get("orientation") == "portrait" else 420, "height": 420 if state.get("orientation") == "portrait" else 297,
            "metersPerUnit": factor, "teams": teams, "zones": zones, "overlaySvg": sanitize_svg(overlay)}


def share_info(owner, project_id):
    with db.connection() as database:
        row = database.execute("SELECT id, enabled, expires_at, current_revision FROM client_shares WHERE owner=? AND project_id=?", (owner, project_id)).fetchone()
        result = dict(row) if row else None
        if result and result["current_revision"]:
            revision = database.execute("SELECT created_at FROM client_revisions WHERE id=?", (result.pop("current_revision"),)).fetchone()
            result["publishedAt"] = revision[0] if revision else None
    return result


def publish(owner, project_id, data):
    project = db.get_project(owner, project_id)
    if not project:
        raise LookupError
    state = data.get("snapshot", project["state"])
    if not isinstance(state, dict):
        raise ValueError("Publication invalide.")
    plan = state.get("planFile") or {}
    if not isinstance(plan, dict):
        raise ValueError("Fond de plan invalide.")
    plan_id = plan.get("id", "")
    if not re.fullmatch(r"[a-fA-F0-9]{32}", str(plan_id)) or not db.has_plan_file(owner, plan_id):
        raise ValueError("Le fond de plan de ce projet est introuvable.")
    metadata = public_metadata(state, data.get("overlaySvg"))
    expires = data.get("expiresOn")
    try:
        expires_at = datetime.combine(date.fromisoformat(expires), daytime.max, timezone.utc).timestamp() if expires else None
    except (TypeError, ValueError) as error:
        raise ValueError("Date de fin invalide.") from error
    if expires_at and expires_at <= time.time():
        raise ValueError("La date de fin doit être à venir.")
    code = data.get("accessCode") or ""
    if not isinstance(code, str) or (code and not 8 <= len(code) <= 128):
        raise ValueError("Le code doit contenir entre 8 et 128 caractères.")
    existing = share_info(owner, project_id)
    share_id = existing["id"] if existing else secrets.token_hex(24)
    generated = not existing and not code
    if generated:
        code = secrets.token_urlsafe(9)
    salt = secrets.token_hex(16) if code else None
    hashed = code_digest(code, salt) if code else None
    revision_id = uuid.uuid4().hex
    target = root_dir() / revision_id
    target.mkdir(parents=True, mode=0o750)
    try:
        source, media_type = preview_file(plan_id)
        # Imported previews are immutable. A hard link keeps snapshots alive on
        # source deletion without duplicating a large PDF on each publication.
        try:
            os.link(source, target / "plan")
        except OSError as error:
            if error.errno != errno.EXDEV:
                raise
            shutil.copyfile(source, target / "plan")
        metadata["planType"] = media_type
        now = time.time()
        metadata["publishedAt"] = now
        metadata["revision"] = revision_id
        with db.connection() as database:
            if existing:
                database.execute("UPDATE client_shares SET enabled=1, expires_at=?, current_revision=? WHERE id=? AND owner=?", (expires_at, revision_id, share_id, owner))
                if code:
                    database.execute("UPDATE client_shares SET salt=?, code_hash=? WHERE id=?", (salt, hashed, share_id))
            else:
                database.execute("INSERT INTO client_shares VALUES(?,?,?,?,?,1,?,?)", (share_id, owner, project_id, salt, hashed, expires_at, revision_id))
            if code:
                database.execute("DELETE FROM client_sessions WHERE share_id=?", (share_id,))
            database.execute("INSERT INTO client_revisions VALUES(?,?,?,?)", (revision_id, share_id, json.dumps(metadata, ensure_ascii=False), now))
        result = share_info(owner, project_id)
        if code:
            result["accessCode"] = code
        return result
    except Exception:
        shutil.rmtree(target)
        raise


def revoke(owner, project_id):
    with db.connection() as database:
        row = database.execute("SELECT id FROM client_shares WHERE owner=? AND project_id=?", (owner, project_id)).fetchone()
        if row:
            database.execute("UPDATE client_shares SET enabled=0 WHERE id=?", (row[0],))
            database.execute("DELETE FROM client_sessions WHERE share_id=?", (row[0],))


def allow_attempt(share_id, address):
    now = time.time()
    keys = [(digest(address), 40), (digest(share_id + ":" + address), 8)]
    with db.connection() as database:
        database.execute("BEGIN IMMEDIATE")
        database.execute("DELETE FROM client_attempts WHERE window_start < ?", (now - 900,))
        database.execute("DELETE FROM client_sessions WHERE expires_at < ?", (now,))
        for key, limit in keys:
            row = database.execute("SELECT count FROM client_attempts WHERE key=?", (key,)).fetchone()
            if row and row[0] >= limit:
                return False
        for key, _ in keys:
            database.execute("INSERT INTO client_attempts VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=count+1", (key, now))
    return True


def active_share(share_id):
    with db.connection() as database:
        row = database.execute("SELECT * FROM client_shares WHERE id=? AND enabled=1 AND (expires_at IS NULL OR expires_at>?)", (share_id, time.time())).fetchone()
    return dict(row) if row else None


def session_token(environ):
    cookie = SimpleCookie()
    try:
        cookie.load(environ.get("HTTP_COOKIE", ""))
        return cookie["crobard_view"].value if "crobard_view" in cookie else ""
    except Exception:
        return ""


def session_valid(environ, share_id):
    token = session_token(environ)
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return False
    with db.connection() as database:
        row = database.execute("SELECT 1 FROM client_sessions WHERE token_hash=? AND share_id=? AND expires_at>?", (digest(token), share_id, time.time())).fetchone()
    return bool(row)


def cookie_header(environ, share_id, token, max_age):
    # Nginx supplies this prefix; it is never accepted from public request headers.
    prefix = environ.get("HTTP_X_CROBARD_BASE", "")
    if len(prefix) > 2048 or not re.fullmatch(r"/[a-zA-Z0-9/_~.%-]*consultation/", prefix):
        prefix = "/consultation/"
    return ("Set-Cookie", f"crobard_view={token}; Path={prefix}api/{share_id}/; Max-Age={max_age}; Secure; HttpOnly; SameSite=Strict")


def public_route(environ, start_response, respond, read_json, send_file):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET").upper()
    match = re.fullmatch(r"/public/([a-f0-9]{48})/(unlock|logout|state|status|snapshot/([a-f0-9]{32})/plan)", path)
    denied = {"error": "Consultation indisponible ou accès expiré. Vérifiez votre lien et votre code."}
    if not match:
        return respond(start_response, HTTPStatus.NOT_FOUND, denied)
    share_id, action, revision_id = match[1], match[2], match[3]
    if (action in {"unlock", "logout"} and method != "POST") or (action not in {"unlock", "logout"} and method != "GET"):
        return respond(start_response, HTTPStatus.METHOD_NOT_ALLOWED, denied)
    # A custom header prevents form-based cross-site session creation or logout.
    if method == "POST" and environ.get("HTTP_X_CROBARD_VIEW") != "1":
        return respond(start_response, HTTPStatus.FORBIDDEN, denied)
    share = active_share(share_id)
    if action == "unlock":
        if not allow_attempt(share_id, environ.get("HTTP_X_REAL_IP") or environ.get("REMOTE_ADDR", "unknown")):
            return respond(start_response, HTTPStatus.TOO_MANY_REQUESTS, {"error": "Trop de tentatives. Réessayez dans 15 minutes."}, [("Retry-After", "900")])
        if int(environ.get("CONTENT_LENGTH") or 0) > 1024:
            return respond(start_response, HTTPStatus.BAD_REQUEST, denied)
        code = read_json(environ).get("code")
        if not isinstance(code, str) or not 8 <= len(code) <= 128:
            return respond(start_response, HTTPStatus.UNAUTHORIZED, denied)
        if not share or not hmac.compare_digest(code_digest(code, share["salt"]), share["code_hash"]):
            return respond(start_response, HTTPStatus.UNAUTHORIZED, denied)
        token = secrets.token_urlsafe(32)
        with db.connection() as database:
            inserted = database.execute("INSERT INTO client_sessions SELECT ?, id, ? FROM client_shares WHERE id=? AND enabled=1 AND code_hash=? AND (expires_at IS NULL OR expires_at>?)", (digest(token), time.time() + SESSION_SECONDS, share_id, share["code_hash"], time.time()))
            if not inserted.rowcount:
                return respond(start_response, HTTPStatus.UNAUTHORIZED, denied)
        return respond(start_response, HTTPStatus.OK, {"opened": True}, [cookie_header(environ, share_id, token, SESSION_SECONDS)])
    if action == "logout":
        with db.connection() as database:
            database.execute("DELETE FROM client_sessions WHERE token_hash=? AND share_id=?", (digest(session_token(environ)), share_id))
        return respond(start_response, HTTPStatus.OK, {"closed": True}, [cookie_header(environ, share_id, "", 0)])
    if not share or not session_valid(environ, share_id):
        return respond(start_response, HTTPStatus.UNAUTHORIZED, denied)
    if action == "status":
        return respond(start_response, HTTPStatus.OK, {"available": True})
    with db.connection() as database:
        revision = database.execute("SELECT * FROM client_revisions WHERE share_id=? AND id=?", (share_id, revision_id or share["current_revision"])).fetchone()
    if not revision:
        return respond(start_response, HTTPStatus.NOT_FOUND, denied)
    metadata = json.loads(revision["metadata"])
    if action == "state":
        return respond(start_response, HTTPStatus.OK, metadata)
    plan = root_dir() / revision_id / "plan"
    if not plan.is_file():
        return respond(start_response, HTTPStatus.NOT_FOUND, denied)
    return send_file(environ, start_response, plan, metadata["planType"], private=True)
