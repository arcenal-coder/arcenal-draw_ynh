import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FrontendTests(unittest.TestCase):
    def test_first_company_uses_generic_default_name(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("{ company: 'Société 1'", javascript)
        self.assertNotIn("{ company: 'INEXCO'", javascript)

    def test_imported_plan_uses_the_entire_a3_sheet(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("Math.min(logicalWidth / baseViewport.width, logicalHeight / baseViewport.height)", javascript)
        self.assertIn("const displayWidth = baseWidth * zoom * cssX", javascript)
        self.assertIn("const displayHeight = baseHeight * zoom * cssY", javascript)

    def test_plan_import_accepts_pdf_png_and_jpeg(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"', markup)
        self.assertIn("Format refusé. Utilisez un fichier PDF, PNG ou JPEG.", javascript)
        self.assertIn('id="plan-preview"', markup)
        self.assertIn("function fallbackToOriginalPdf()", javascript)

    def test_import_help_and_conversion_progress_are_visible(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("DWG To PDF.pc3", markup)
        self.assertIn("PDFSHX", markup)
        self.assertIn('id="import-progress"', markup)
        self.assertIn("function uploadPlanFile(file)", javascript)
        self.assertIn("Analyse du PDF et conversion SVG", javascript)

    def test_measurements_are_persisted_and_use_calibration(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("measurements: []", javascript)
        self.assertIn("metersPerNativeUnit", javascript)
        self.assertIn("function placeMeasurement", javascript)
        self.assertIn('id="measurement-layer"', markup)

    def test_scale_setup_uses_two_clicks_and_one_meter_value(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="scale-layer"', markup)
        self.assertIn("function beginScaleSetup", javascript)
        self.assertIn("function placeScalePoint", javascript)
        self.assertIn("realDistance / scaleSetup.nativeDistance", javascript)
        self.assertNotIn('id="source-unit"', markup)
        self.assertNotIn('id="native-distance"', markup)
        self.assertIn('class="scale-guide-cross"', javascript)
        self.assertNotIn('class="scale-guide-point"', javascript)
        self.assertEqual(markup.count('>Calibrer</button>'), 2)
        self.assertIn("classList.add('scale-setting')", javascript)
        self.assertIn('x1="-0.45"', javascript)
        self.assertIn("function metersToPlanUnits(meters)", javascript)
        self.assertIn("metersToPlanUnits(segmentMeters) * scale", javascript)
        self.assertIn("element.setAttribute('r', metersToPlanUnits(circle.radius))", javascript)

    def test_home_libraries_are_limited_searchable_and_reusable(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="project-search"', markup)
        self.assertIn('id="archive-search"', markup)
        self.assertIn('id="exploitable-plans"', markup)
        self.assertIn("source.slice(0, 3)", javascript)
        self.assertIn("normalized.slice(0, 3)", javascript)
        self.assertIn("apiRequest('imports')", javascript)
        self.assertIn('data-delete-archive', javascript)
        self.assertIn('data-delete-plan', javascript)
        self.assertIn("method: 'DELETE'", javascript)

    def test_title_block_can_be_hidden_and_is_persisted(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="settings-title-block"', markup)
        self.assertIn("showTitleBlock: true", javascript)
        self.assertIn("titleBlock.style.display = state.showTitleBlock ? '' : 'none'", javascript)

    def test_title_block_omits_visible_team_count_and_zoom_has_step_buttons(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Équipes visibles", javascript)
        self.assertIn('id="zoom-out"', markup)
        self.assertIn('id="zoom-in"', markup)
        self.assertIn("function setPlanZoom(value)", javascript)

    def test_import_ui_resets_and_plan_library_loads_independently(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("setImportProgress('hidden')", javascript)
        self.assertIn("setImportStatus();", javascript)
        self.assertIn("Promise.allSettled", javascript)
        self.assertIn("reusablePlans = [pendingPlanImport", javascript)


if __name__ == "__main__":
    unittest.main()
