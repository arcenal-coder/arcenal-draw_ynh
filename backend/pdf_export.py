import pathlib
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


POINTS_PER_MM = 72 / 25.4
MAX_OVERLAY_BYTES = 24 * 1024 * 1024


class ExportErrorSafe(Exception):
    pass


def _pdf_library():
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf._page import PageObject
    except ImportError:
        try:
            import PyPDF2
            from PyPDF2._page import PageObject
            PdfReader = PyPDF2.PdfReader if hasattr(PyPDF2, "PdfReader") else PyPDF2.PdfFileReader
            PdfWriter = PyPDF2.PdfWriter if hasattr(PyPDF2, "PdfWriter") else PyPDF2.PdfFileWriter
        except ImportError as error:
            raise ExportErrorSafe("Le moteur PDF vectoriel n’est pas installé sur le serveur.") from error
    return PdfReader, PdfWriter, PageObject


def _validate_svg(markup):
    encoded = markup.encode("utf-8")
    if not encoded or len(encoded) > MAX_OVERLAY_BYTES:
        raise ExportErrorSafe("Le calque graphique est vide ou trop volumineux.")
    if "<!DOCTYPE" in markup.upper() or "<!ENTITY" in markup.upper():
        raise ExportErrorSafe("Le calque graphique contient une déclaration interdite.")
    try:
        root = ET.fromstring(markup)
    except ET.ParseError as error:
        raise ExportErrorSafe("Le calque graphique est invalide.") from error
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "foreignobject"}:
            raise ExportErrorSafe("Le calque graphique contient un élément interdit.")
        for key, value in element.attrib.items():
            if key.rsplit("}", 1)[-1].lower() == "href" and not value.startswith(("data:", "#")):
                raise ExportErrorSafe("Le calque graphique contient une ressource externe interdite.")
    return encoded


def _svg_to_pdf(markup, destination):
    executable = shutil.which("rsvg-convert")
    if not executable:
        raise ExportErrorSafe("Le moteur SVG vectoriel n’est pas installé sur le serveur.")
    encoded = _validate_svg(markup)
    try:
        subprocess.run(
            [executable, "--format=pdf", f"--output={destination}"],
            input=encoded,
            check=True,
            timeout=120,
            capture_output=True,
        )
    except (subprocess.SubprocessError, OSError) as error:
        raise ExportErrorSafe("La conversion du calque vectoriel a échoué.") from error
    if not destination.is_file() or destination.stat().st_size < 10:
        raise ExportErrorSafe("Le calque vectoriel produit est vide.")


def build_hybrid_pdf(source_path, overlay_svg, orientation, zoom, pan_x, pan_y):
    PdfReader, PdfWriter, PageObject = _pdf_library()
    width_mm, height_mm = ((297, 420) if orientation == "portrait" else (420, 297))
    page_width = width_mm * POINTS_PER_MM
    page_height = height_mm * POINTS_PER_MM
    try:
        zoom = min(50.0, max(1.0, float(zoom)))
        pan_x = float(pan_x)
        pan_y = float(pan_y)
    except (TypeError, ValueError) as error:
        raise ExportErrorSafe("Position ou zoom du plan invalide.") from error

    with tempfile.TemporaryDirectory(prefix="arcenal-pdf-") as directory:
        overlay_path = pathlib.Path(directory) / "overlay.pdf"
        _svg_to_pdf(overlay_svg, overlay_path)
        try:
            source_reader = PdfReader(str(source_path), strict=False)
            overlay_reader = PdfReader(str(overlay_path), strict=False)
            source_page = source_reader.pages[0]
            overlay_page = overlay_reader.pages[0]
            if hasattr(source_page, "transfer_rotation_to_content"):
                source_page.transfer_rotation_to_content()
            source_box = source_page.cropbox if hasattr(source_page, "cropbox") else source_page.cropBox
            source_left = float(source_box.left)
            source_bottom = float(source_box.bottom)
            source_width = float(source_box.width)
            source_height = float(source_box.height)
            fit = min(width_mm / source_width, height_mm / source_height)
            base_width = source_width * fit
            base_height = source_height * fit
            base_x = (width_mm - base_width) / 2
            base_y = (height_mm - base_height) / 2
            logical_x = 150 + pan_x + zoom * (base_x - 150)
            logical_y = 135 + pan_y + zoom * (base_y - 135)
            scale = fit * zoom * POINTS_PER_MM
            translate_x = logical_x * POINTS_PER_MM
            translate_y = page_height - logical_y * POINTS_PER_MM - source_height * scale

            create_blank = PageObject.create_blank_page if hasattr(PageObject, "create_blank_page") else PageObject.createBlankPage
            output_page = create_blank(width=page_width, height=page_height)
            matrix = (scale, 0, 0, scale, translate_x - source_left * scale, translate_y - source_bottom * scale)
            if hasattr(output_page, "merge_transformed_page"):
                output_page.merge_transformed_page(source_page, matrix, expand=False)
                output_page.merge_page(overlay_page)
            else:
                output_page.mergeTransformedPage(source_page, matrix, expand=False)
                output_page.mergePage(overlay_page)
            writer = PdfWriter()
            add_page = writer.add_page if hasattr(writer, "add_page") else writer.addPage
            add_metadata = writer.add_metadata if hasattr(writer, "add_metadata") else writer.addMetadata
            add_page(output_page)
            add_metadata({"/Producer": "ARCenal DRAW", "/Title": "Plan de contrôle gammagraphique"})
            output_path = pathlib.Path(directory) / "export.pdf"
            with output_path.open("wb") as stream:
                writer.write(stream)
            result = output_path.read_bytes()
        except ExportErrorSafe:
            raise
        except Exception as error:
            raise ExportErrorSafe("La composition du PDF vectoriel a échoué.") from error
    if not result.startswith(b"%PDF-"):
        raise ExportErrorSafe("Le PDF vectoriel produit est invalide.")
    return result
