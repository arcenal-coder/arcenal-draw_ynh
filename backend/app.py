import json
import logging
import os
import re
import uuid
from http import HTTPStatus
from urllib.parse import unquote

from backend import db
from backend.importer import ImportErrorSafe, convert_upload, preview_file, store_upload


MAX_JSON_BYTES = 12 * 1024 * 1024
ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,80}$")
LOGGER = logging.getLogger("arcenal_draw")


def response(start_response, status, payload=None, headers=None):
    body = b"" if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    response_headers = [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))]
    response_headers.extend(headers or [])
    start_response(f"{status.value} {status.phrase}", response_headers)
    return [body]


def file_response(start_response, path, media_type):
    size = path.stat().st_size
    start_response("200 OK", [
        ("Content-Type", media_type),
        ("Content-Length", str(size)),
        ("Cache-Control", "private, max-age=86400"),
        ("X-Content-Type-Options", "nosniff"),
    ])
    def chunks():
        with path.open("rb") as source:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
    return chunks()


def read_json(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError as error:
        raise ValueError("Longueur invalide.") from error
    if length < 1 or length > MAX_JSON_BYTES:
        raise ValueError("Corps JSON vide ou trop volumineux.")
    return json.loads(environ["wsgi.input"].read(length).decode("utf-8"))


def current_user(environ):
    user = environ.get("HTTP_REMOTE_USER") or environ.get("HTTP_AUTH_USER")
    if user:
        return user[:150]
    if os.environ.get("ARCENAL_ALLOW_ANONYMOUS") == "1":
        return "local"
    return None


def application(environ, start_response):
    try:
        return route(environ, start_response)
    except ImportErrorSafe as error:
        return response(start_response, HTTPStatus.BAD_REQUEST, {"error": str(error)})
    except (ValueError, json.JSONDecodeError) as error:
        return response(start_response, HTTPStatus.BAD_REQUEST, {"error": str(error)})
    except Exception:
        LOGGER.exception("Unhandled API error")
        return response(start_response, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Erreur interne."})


def route(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = unquote(environ.get("PATH_INFO") or "/")
    if path == "/api/health" and method == "GET":
        return response(start_response, HTTPStatus.OK, {"status": "ok"})

    owner = current_user(environ)
    if not owner:
        return response(start_response, HTTPStatus.UNAUTHORIZED, {"error": "Authentification requise."})

    if path == "/api/projects" and method == "GET":
        return response(start_response, HTTPStatus.OK, {"projects": db.list_projects(owner)})

    project_match = re.fullmatch(r"/api/projects/([^/]+)", path)
    if project_match:
        project_id = project_match.group(1)
        if not ID_PATTERN.fullmatch(project_id):
            return response(start_response, HTTPStatus.BAD_REQUEST, {"error": "Identifiant invalide."})
        if method == "GET":
            project = db.get_project(owner, project_id)
            return response(start_response, HTTPStatus.OK, project) if project else response(start_response, HTTPStatus.NOT_FOUND, {"error": "Projet introuvable."})
        if method == "PUT":
            state = read_json(environ)
            project = db.save_project(owner, project_id, state)
            return response(start_response, HTTPStatus.OK, project)

    if path == "/api/archives" and method == "GET":
        return response(start_response, HTTPStatus.OK, {"archives": db.list_archives(owner)})
    if path == "/api/archives" and method == "POST":
        data = read_json(environ)
        archive_id = str(data.get("id") or uuid.uuid4().hex)
        if not ID_PATTERN.fullmatch(archive_id):
            raise ValueError("Identifiant d’archive invalide.")
        db.save_archive(owner, archive_id, data.get("projectId"), data.get("exportName") or "Export PDF", data.get("state") or {})
        return response(start_response, HTTPStatus.CREATED, {"id": archive_id})

    archive_match = re.fullmatch(r"/api/archives/([^/]+)", path)
    if archive_match and method == "GET":
        archive_id = archive_match.group(1)
        if not ID_PATTERN.fullmatch(archive_id):
            return response(start_response, HTTPStatus.BAD_REQUEST, {"error": "Identifiant invalide."})
        archive = db.get_archive(owner, archive_id)
        return response(start_response, HTTPStatus.OK, archive) if archive else response(start_response, HTTPStatus.NOT_FOUND, {"error": "Archive introuvable."})

    if path == "/api/imports" and method == "POST":
        filename = unquote(environ.get("HTTP_X_FILENAME") or "plan")
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError as error:
            raise ImportErrorSafe("Longueur de fichier invalide.") from error
        upload = store_upload(environ["wsgi.input"], filename, length)
        converted = convert_upload(upload)
        public = {key: value for key, value in converted.items() if key not in {"path", "convertedPath"}}
        return response(start_response, HTTPStatus.CREATED, public)

    preview_match = re.fullmatch(r"/api/imports/([a-fA-F0-9]{32})/preview", path)
    if preview_match and method == "GET":
        try:
            preview, media_type = preview_file(preview_match.group(1))
        except FileNotFoundError:
            return response(start_response, HTTPStatus.NOT_FOUND, {"error": "Aperçu introuvable."})
        return file_response(start_response, preview, media_type)

    return response(start_response, HTTPStatus.NOT_FOUND, {"error": "Route introuvable."})


db.initialize()
