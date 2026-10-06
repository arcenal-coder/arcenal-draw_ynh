import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import uuid


UPLOAD_DIR = pathlib.Path(os.environ.get("ARCENAL_UPLOAD_DIR", "/var/lib/arcenal-draw/uploads"))
MAX_UPLOAD_BYTES = int(os.environ.get("ARCENAL_MAX_UPLOAD_BYTES", 100 * 1024 * 1024))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


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
    signatures = {
        ".pdf": b"%PDF-" in header,
        ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
    }
    if not signatures[extension]:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise ImportErrorSafe("Le contenu du fichier ne correspond pas à son format.")
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
        "originalUrl": f"imports/{upload['id']}/original",
    }


def _convert_pdf_to_svg(source, output, timeout=120):
    executable = shutil.which("pdftocairo")
    if not executable:
        return False
    output.unlink(missing_ok=True)
    try:
        subprocess.run(
            [executable, "-svg", "-f", "1", "-l", "1", str(source), str(output)],
            check=True,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, OSError):
        output.unlink(missing_ok=True)
        return False
    if not output.is_file() or output.stat().st_size == 0:
        return False
    markup = output.read_text(encoding="utf-8", errors="ignore").lower()
    root_match = re.search(r"<svg\b([^>]*)>", markup)
    dimensions = root_match.group(1) if root_match else ""
    view_box = re.search(r"viewbox=[\"']\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)", dimensions)
    width = re.search(r"\bwidth=[\"']\s*([\d.]+)", dimensions)
    height = re.search(r"\bheight=[\"']\s*([\d.]+)", dimensions)
    valid_size = bool(view_box and float(view_box.group(1)) > 0 and float(view_box.group(2)) > 0)
    valid_size = valid_size or bool(width and height and float(width.group(1)) > 0 and float(height.group(1)) > 0)
    vector_elements = sum(markup.count(tag) for tag in ("<path", "<text", "<use", "<line", "<polyline", "<polygon"))
    if not valid_size or ("<image" in markup and vector_elements < 20):
        output.unlink(missing_ok=True)
        return False
    return vector_elements > 0


def convert_upload(upload):
    source = pathlib.Path(upload["path"])
    extension = upload["extension"]
    if extension == ".pdf":
        preview = source.with_name("preview.svg")
        if _convert_pdf_to_svg(source, preview):
            return _preview_result(upload, preview, "image/svg+xml", "PDF vectoriel → SVG")
        return _preview_result(upload, source, "application/pdf", "PDF natif optimisé")
    media_type = "image/png" if extension == ".png" else "image/jpeg"
    return _preview_result(upload, source, media_type, "Image native optimisée")


def preview_file(upload_id):
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise ImportErrorSafe("Identifiant d’import invalide.")
    directory = UPLOAD_DIR / upload_id
    for name, media_type in (
        ("preview.svg", "image/svg+xml"),
        ("original.pdf", "application/pdf"),
        ("plan.pdf", "application/pdf"),
        ("original.png", "image/png"),
        ("original.jpg", "image/jpeg"),
        ("original.jpeg", "image/jpeg"),
    ):
        candidate = directory / name
        if candidate.is_file():
            return candidate, media_type
    raise FileNotFoundError


def original_file(upload_id):
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise ImportErrorSafe("Identifiant d’import invalide.")
    directory = UPLOAD_DIR / upload_id
    for name, media_type in (
        ("original.pdf", "application/pdf"),
        ("original.png", "image/png"),
        ("original.jpg", "image/jpeg"),
        ("original.jpeg", "image/jpeg"),
    ):
        candidate = directory / name
        if candidate.is_file():
            return candidate, media_type
    raise FileNotFoundError


def delete_import(upload_id):
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise ImportErrorSafe("Identifiant d’import invalide.")
    directory = UPLOAD_DIR / upload_id
    if directory.is_dir():
        shutil.rmtree(directory)
