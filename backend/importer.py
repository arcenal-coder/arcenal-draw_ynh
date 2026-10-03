import hashlib
import html
import math
import mimetypes
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


def _run(command, label, timeout=120):
    try:
        subprocess.run(command, check=True, timeout=timeout, capture_output=True, text=True)
    except (subprocess.SubprocessError, OSError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise ImportErrorSafe(f"{label} impossible : {detail[:240]}") from error


def _points_from_entity(entity):
    kind = entity.dxftype()
    if kind == "LINE":
        return [(entity.dxf.start.x, entity.dxf.start.y), (entity.dxf.end.x, entity.dxf.end.y)]
    if kind == "LWPOLYLINE":
        return [(point[0], point[1]) for point in entity.get_points("xy")]
    if kind == "POLYLINE":
        return [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
    if kind in {"CIRCLE", "ARC"}:
        center, radius = entity.dxf.center, float(entity.dxf.radius)
        return [(center.x - radius, center.y - radius), (center.x + radius, center.y + radius)]
    if kind in {"TEXT", "MTEXT"}:
        point = entity.dxf.insert
        return [(point.x, point.y)]
    try:
        return [(point.x, point.y) for point in entity.flattening(0.1)]
    except (AttributeError, TypeError, ValueError):
        return []


def _expanded_entities(layout):
    pending = list(layout)
    while pending:
        entity = pending.pop(0)
        if entity.dxftype() in {"INSERT", "DIMENSION"}:
            try:
                pending[0:0] = list(entity.virtual_entities())
                continue
            except (AttributeError, TypeError, ValueError):
                pass
        yield entity


def _dxf_to_svg(source, output):
    try:
        import ezdxf
    except ImportError as error:
        raise ImportErrorSafe("Le moteur DXF ezdxf n’est pas installé sur le serveur.") from error
    try:
        document = ezdxf.readfile(source)
        entities = list(_expanded_entities(document.modelspace()))
    except Exception as error:
        raise ImportErrorSafe(f"Lecture DXF impossible : {str(error)[:240]}") from error

    all_points = [point for entity in entities for point in _points_from_entity(entity)]
    if not all_points:
        raise ImportErrorSafe("Le fichier DXF ne contient aucun tracé 2D exploitable.")
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    width = max(max_x - min_x, 1e-9)
    height = max(max_y - min_y, 1e-9)
    scale = min(330 / width, 240 / height)
    pad_x = (330 - width * scale) / 2
    pad_y = (240 - height * scale) / 2

    def xy(point):
        return pad_x + (point[0] - min_x) * scale, pad_y + (max_y - point[1]) * scale

    shapes = []
    for entity in entities:
        kind = entity.dxftype()
        points = _points_from_entity(entity)
        if kind == "LINE" and len(points) == 2:
            start, end = xy(points[0]), xy(points[1])
            shapes.append(f'<line x1="{start[0]:.3f}" y1="{start[1]:.3f}" x2="{end[0]:.3f}" y2="{end[1]:.3f}"/>')
        elif kind in {"LWPOLYLINE", "POLYLINE"} and len(points) > 1:
            mapped = " ".join(f"{x:.3f},{y:.3f}" for x, y in map(xy, points))
            shapes.append(f'<polyline points="{mapped}" fill="none"/>')
        elif kind == "CIRCLE":
            center = xy((entity.dxf.center.x, entity.dxf.center.y))
            shapes.append(f'<circle cx="{center[0]:.3f}" cy="{center[1]:.3f}" r="{float(entity.dxf.radius) * scale:.3f}"/>')
        elif kind == "ARC":
            center = entity.dxf.center
            radius = float(entity.dxf.radius)
            start_angle, end_angle = math.radians(entity.dxf.start_angle), math.radians(entity.dxf.end_angle)
            start = xy((center.x + radius * math.cos(start_angle), center.y + radius * math.sin(start_angle)))
            end = xy((center.x + radius * math.cos(end_angle), center.y + radius * math.sin(end_angle)))
            large = 1 if (entity.dxf.end_angle - entity.dxf.start_angle) % 360 > 180 else 0
            shapes.append(f'<path d="M{start[0]:.3f},{start[1]:.3f} A{radius * scale:.3f},{radius * scale:.3f} 0 {large} 0 {end[0]:.3f},{end[1]:.3f}"/>')
        elif kind in {"TEXT", "MTEXT"} and points:
            position = xy(points[0])
            value = entity.plain_text() if kind == "MTEXT" else entity.dxf.text
            shapes.append(f'<text x="{position[0]:.3f}" y="{position[1]:.3f}" fill="#33434d" stroke="none" font-size="3">{html.escape(str(value))}</text>')
        elif len(points) > 1:
            mapped = " ".join(f"{x:.3f},{y:.3f}" for x, y in map(xy, points))
            shapes.append(f'<polyline points="{mapped}" fill="none"/>')

    svg = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 330 240">'
           '<rect width="330" height="240" fill="white"/>'
           '<g fill="none" stroke="#667680" stroke-width="0.45">'
           + "".join(shapes) + '</g></svg>')
    output.write_text(svg, encoding="utf-8")


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
    extension = upload["extension"]
    if extension in {".png", ".jpg", ".jpeg"}:
        return _preview_result(upload, source, mimetypes.guess_type(source.name)[0] or "image/jpeg", "image native")
    if extension == ".pdf":
        return _preview_result(upload, source, "application/pdf", "PDF natif")
    if extension == ".dwg":
        configured_executable = os.environ.get("ARCENAL_DWG2DXF", "")
        executable = configured_executable if configured_executable and os.access(configured_executable, os.X_OK) else shutil.which("dwg2dxf")
        if not executable:
            raise ImportErrorSafe("Le moteur DWG LibreDWG (dwg2dxf) n’est pas disponible sur ce serveur YunoHost.")
        source_dxf = source.with_name("converted.dxf")
        _run([executable, "-o", str(source_dxf), str(source)], "Conversion DWG")
    else:
        source_dxf = source
    preview = source.with_name("preview.svg")
    _dxf_to_svg(source_dxf, preview)
    executable = shutil.which("rsvg-convert")
    if not executable:
        raise ImportErrorSafe("Le convertisseur PDF vectoriel librsvg n’est pas installé sur le serveur.")
    pdf = source.with_name("plan.pdf")
    _run([executable, "-f", "pdf", "-o", str(pdf), str(preview)], "Conversion en PDF vectoriel")
    preview.unlink(missing_ok=True)
    return _preview_result(upload, pdf, "application/pdf", "LibreDWG + PDF vectoriel" if extension == ".dwg" else "DXF + PDF vectoriel")


def preview_file(upload_id):
    if not upload_id.isalnum() or len(upload_id) != 32:
        raise ImportErrorSafe("Identifiant d’import invalide.")
    directory = UPLOAD_DIR / upload_id
    for name in ("plan.pdf", "original.pdf", "original.png", "original.jpg", "original.jpeg", "preview.svg", "preview.png"):
        candidate = directory / name
        if candidate.is_file():
            return candidate, mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    raise FileNotFoundError
