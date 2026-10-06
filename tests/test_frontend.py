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

    def test_measurements_are_persisted_and_use_calibration(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("measurements: []", javascript)
        self.assertIn("metersPerNativeUnit", javascript)
        self.assertIn("function placeMeasurement", javascript)
        self.assertIn('id="measurement-layer"', markup)


if __name__ == "__main__":
    unittest.main()
