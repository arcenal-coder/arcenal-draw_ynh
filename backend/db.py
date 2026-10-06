import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


DB_PATH = os.environ.get("ARCENAL_DB_PATH", "/var/lib/arcenal-draw/arcenal.sqlite3")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    database = sqlite3.connect(DB_PATH, timeout=10)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    database.execute("PRAGMA journal_mode = WAL")
    try:
        yield database
        database.commit()
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def initialize():
    os.makedirs(os.path.dirname(DB_PATH), mode=0o750, exist_ok=True)
    with connection() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS projects_owner_updated
                ON projects(owner, updated_at DESC);

            CREATE TABLE IF NOT EXISTS archives (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                owner TEXT NOT NULL,
                export_name TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS archives_owner_created
                ON archives(owner, created_at DESC);

            CREATE TABLE IF NOT EXISTS plan_files (
                id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                original_name TEXT NOT NULL,
                media_type TEXT NOT NULL,
                original_path TEXT NOT NULL,
                converted_path TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL
            );
            """
        )


def list_projects(owner):
    with connection() as database:
        rows = database.execute(
            "SELECT id, name, location, created_at, updated_at FROM projects WHERE owner = ? ORDER BY updated_at DESC",
            (owner,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_project(owner, project_id):
    with connection() as database:
        row = database.execute(
            "SELECT * FROM projects WHERE owner = ? AND id = ?", (owner, project_id)
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["state"] = json.loads(result.pop("state_json"))
    return result


def save_project(owner, project_id, state):
    now = utc_now()
    name = str(state.get("name") or "Plan sans titre")[:200]
    location = str(state.get("location") or "")[:300]
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    with connection() as database:
        database.execute(
            """
            INSERT INTO projects(id, owner, name, location, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                location = excluded.location,
                state_json = excluded.state_json,
                updated_at = excluded.updated_at
            WHERE projects.owner = excluded.owner
            """,
            (project_id, owner, name, location, payload, now, now),
        )
    return get_project(owner, project_id)


def list_archives(owner, limit=50):
    with connection() as database:
        rows = database.execute(
            "SELECT id, project_id, export_name, created_at FROM archives WHERE owner = ? ORDER BY created_at DESC LIMIT ?",
            (owner, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def save_plan_file(owner, plan):
    preview_path = os.path.join(os.path.dirname(plan["path"]), plan["preview"])
    with connection() as database:
        database.execute(
            """
            INSERT INTO plan_files(id, owner, original_name, media_type, original_path, converted_path, status, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)
            ON CONFLICT(id) DO UPDATE SET
                original_name = excluded.original_name,
                media_type = excluded.media_type,
                original_path = excluded.original_path,
                converted_path = excluded.converted_path,
                status = excluded.status,
                error_message = NULL
            WHERE plan_files.owner = excluded.owner
            """,
            (plan["id"], owner, plan["name"], plan["previewType"], plan["path"], preview_path, plan.get("status", "converted"), utc_now()),
        )


def list_plan_files(owner, limit=100):
    with connection() as database:
        rows = database.execute(
            """SELECT id, original_name, media_type, status, created_at
               FROM plan_files WHERE owner = ? AND status = 'converted'
               ORDER BY created_at DESC LIMIT ?""",
            (owner, limit),
        ).fetchall()
    plans = []
    for row in rows:
        extension = os.path.splitext(row["original_name"])[1].lower()
        preview_type = row["media_type"]
        plans.append({
            "id": row["id"], "name": row["original_name"], "extension": extension,
            "requiresCalibration": True, "status": row["status"],
            "conversion": "PDF vectoriel → SVG" if preview_type == "image/svg+xml" else ("PDF natif optimisé" if preview_type == "application/pdf" else "Image native optimisée"),
            "previewType": preview_type,
            "previewUrl": f"imports/{row['id']}/preview",
            "originalUrl": f"imports/{row['id']}/original",
            "createdAt": row["created_at"],
        })
    return plans


def get_archive(owner, archive_id):
    with connection() as database:
        row = database.execute(
            "SELECT * FROM archives WHERE owner = ? AND id = ?", (owner, archive_id)
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["state"] = json.loads(result.pop("state_json"))
    return result


def save_archive(owner, archive_id, project_id, export_name, state):
    payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    with connection() as database:
        if project_id:
            exists = database.execute(
                "SELECT 1 FROM projects WHERE id = ? AND owner = ?", (project_id, owner)
            ).fetchone()
            if not exists:
                project_id = None
        database.execute(
            "INSERT INTO archives(id, project_id, owner, export_name, state_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (archive_id, project_id, owner, str(export_name)[:300], payload, utc_now()),
        )
