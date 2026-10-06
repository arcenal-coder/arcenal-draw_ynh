import hashlib
import mimetypes
import os
import pathlib
import shutil
import uuid


UPLOAD_DIR = pathlib.Path(os.environ.get("ARCENAL_UPLOAD_DIR", "/var/lib/arcenal-draw/uploads"))
MAX_UPLOAD_BYTES = int(os.environ.get("ARCENAL_MAX_UPLOAD_BYTES", 100 * 1024 * 1024))
ALLOWED_EXTENSIONS = {".pdf"}


class ImportErrorSafe(Exception):
    pass


def safe_name(name):
    candidate = pathlib.Path(name or "plan").name
    return "".join(character for character in candidate if character.isalnum() or character in " ._-()").strip()[:180] or "plan"


def store_upload(stream, filename, content_length):
    extension = pathlib.Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ImportErrorSafe("Format non pris en charge.")
    if content_length is None or content_length < 1 or content_length > MAX_UPLOAD_BYTES:
        raise ImportErrorSafe("Taille du fichier invalide ou supérieure à 100 Mo.")

    upload_id = uuid.uuid4().hex
    target_dir = UPLOAD_DIR / upload_id
    target_dir.mkdir(parents=True, mode=0o750)
    target = target_dir / f"original{extension}"
    digest = hashlib.sha256()
    remaining = content_length
    header = b""
    with target.open("xb") as destination:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            if len(header) < 1024:
                header = (header + chunk)[:1024]
            destination.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    if remaining:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ImportErrorSafe("Téléversement incomplet.")
    if b"%PDF-" not in header:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ImportErrorSafe("Le fichier sélectionné n’est pas un PDF valide.")
    return {
        "id": upload_id,
        "name": safe_name(filename),
        "extension": extension,
        "path": str(target),
        "sha256": digest.hexdigest(),
        "requiresCalibration": True,
    }


def _preview_result(upload, preview, media_type, conversion):
    return {
        **upload,
        "status": "converted",
        "conversion": conversion,
        "preview": preview.name,
        "previewType": media_type,
        "previewUrl": f"imports/{upload['id']}/preview",
    }


def convert_upload(upload):
    source = pathlib.Path(upload["path"])
    return _preview_result(upload, source, "application/pdf", "PDF natif")


def preview_file(upload_id):
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise ImportErrorSafe("Identifiant d’import invalide.")
    directory = UPLOAD_DIR / upload_id
    candidate = directory / "original.pdf"
    if candidate.is_file():
        return candidate, mimetypes.guess_type(candidate.name)[0] or "application/pdf"
    raise FileNotFoundError
