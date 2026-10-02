import hashlib
import os
import pathlib
import shutil
import subprocess
import uuid


UPLOAD_DIR = pathlib.Path(os.environ.get("ARCENAL_UPLOAD_DIR", "/var/lib/arcenal-draw/uploads"))
MAX_UPLOAD_BYTES = int(os.environ.get("ARCENAL_MAX_UPLOAD_BYTES", 100 * 1024 * 1024))
ALLOWED_EXTENSIONS = {".dwg", ".dxf", ".pdf", ".png", ".jpg", ".jpeg"}


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
    with target.open("xb") as destination:
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            destination.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    if remaining:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ImportErrorSafe("Téléversement incomplet.")
    return {
        "id": upload_id,
        "name": safe_name(filename),
        "extension": extension,
        "path": str(target),
        "sha256": digest.hexdigest(),
        "requiresCalibration": extension in {".pdf", ".png", ".jpg", ".jpeg"},
    }


def convert_upload(upload):
    source = pathlib.Path(upload["path"])
    extension = upload["extension"]
    if extension == ".dwg":
        executable = shutil.which("dwgread")
        if not executable:
            return {**upload, "status": "stored", "conversion": "LibreDWG indisponible"}
        output = source.with_name("plan.json")
        command = [executable, "-O", "JSON", "-o", str(output), str(source)]
        try:
            subprocess.run(command, check=True, timeout=60, capture_output=True, text=True)
        except (subprocess.SubprocessError, OSError) as error:
            raise ImportErrorSafe(f"Conversion DWG impossible : {str(error)[:180]}") from error
        return {**upload, "status": "converted", "convertedPath": str(output)}
    return {**upload, "status": "stored"}

