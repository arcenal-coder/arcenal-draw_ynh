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

    def test_import_hint_and_conversion_progress_are_visible(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('PDF (désactiver « Tracer avec les épaisseurs d’objet »)', markup)
        self.assertNotIn("MODE D’EMPLOI AUTOCAD", markup)
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
        self.assertEqual(markup.count('>Calibrer</button>'), 3)
        self.assertIn("classList.add('scale-setting')", javascript)
        self.assertIn('x1="-0.45"', javascript)
        self.assertIn("function metersToPlanUnits(meters)", javascript)
        self.assertIn("metersToPlanUnits(segmentMeters) * scale", javascript)
        self.assertIn("element.setAttribute('r', metersToPlanUnits(circle.radius))", javascript)
        self.assertIn('id="scale-distance-prompt"', markup)
        self.assertIn("scaleDistancePrompt.hidden = false", javascript)

    def test_new_import_prompts_for_calibration_but_reusable_base_keeps_it(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="calibration-intro-dialog"', markup)
        self.assertIn("Avant de commencer, calibrez le plan", markup)
        self.assertIn("function openPlanProject(plan)", javascript)
        self.assertIn("plan.calibration?.metersPerNativeUnit > 0", javascript)
        self.assertIn("method: 'PUT'", javascript)

    def test_home_libraries_are_limited_searchable_and_reusable(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="project-search"', markup)
        self.assertIn('id="archive-search"', markup)
        self.assertIn('id="exploitable-plans"', markup)
        self.assertIn("source.slice(0, 5)", javascript)
        self.assertIn("normalized.slice(0, 3)", javascript)
        self.assertIn("apiRequest('imports')", javascript)
        self.assertIn('data-delete-archive', javascript)
        self.assertIn('data-delete-plan', javascript)
        self.assertIn("method: 'DELETE'", javascript)

    def test_project_restore_reconciles_the_plan_and_uses_a_snapshot(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("function projectDisplayName", javascript)
        self.assertIn("const projectSnapshot = JSON.parse(JSON.stringify(state))", javascript)
        self.assertIn("async function restoreProject(project)", javascript)
        self.assertIn("restored.planFile?.id", javascript)
        self.assertIn("restored.planFile = { ...restored.planFile, ...currentPlan }", javascript)
        self.assertIn("clearPdfRenderer();", javascript)

    def test_author_settings_are_on_home_and_pdf_signatures_are_rendered(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="home-author-card"', markup)
        self.assertEqual(markup.count('id="author-name"'), 1)
        self.assertIn("async function readPdfAsImage(file)", javascript)
        self.assertIn("dataUrl: await readPdfAsImage(file)", javascript)
        self.assertIn("AUTHOR_PROFILE_KEY", javascript)
        self.assertIn("saveAuthorProfile()", javascript)

    def test_home_waits_for_current_project_save_before_refreshing(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("async function openHome()", javascript)
        self.assertIn("clearTimeout(serverSaveTimer)", javascript)
        self.assertIn("await refreshServerLibrary()", javascript)
        self.assertIn("clearTimeout(serverSaveTimer);\n  const restored", javascript)

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
        self.assertIn('id="plan-zoom" type="range" min="1" max="50" step="0.5"', markup)
        self.assertIn('id="settings-zoom" type="range" min="1" max="50" step="0.5"', markup)
        self.assertIn("Math.max(100, Math.min(5000", javascript)
        self.assertIn("zoomLabel()", javascript)

    def test_escape_cancels_current_action_and_selection(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("function cancelCurrentAction()", javascript)
        self.assertIn("event.key === 'Escape'", javascript)
        self.assertIn("setTool('select');", javascript)

    def test_obsolete_impact_code_setting_is_removed(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('id="settings-labels"', markup)
        self.assertNotIn("showImpactLabels", javascript)

    def test_import_ui_resets_and_plan_library_loads_independently(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("setImportProgress('hidden')", javascript)
        self.assertIn("setImportStatus();", javascript)
        self.assertIn("Promise.allSettled", javascript)
        self.assertIn("reusablePlans = [pendingPlanImport", javascript)

    def test_navigation_uses_fast_preview_then_deferred_precise_render(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="pdf-surface"', markup)
        self.assertIn("function scheduleInteractionUpdate()", javascript)
        self.assertIn("requestAnimationFrame", javascript)
        self.assertIn("function finalizeNavigation(delay = 140)", javascript)
        self.assertIn("updatePdfSurfaceTransform();", javascript)

    def test_impact_marker_keeps_a_constant_visual_size_while_zooming(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("impactLayer.querySelectorAll('.impact-marker')", javascript)
        self.assertIn("scale(${1 / scale})", javascript)
        self.assertIn("marker.dataset.x = circle.cx", javascript)

    def test_editable_team_card_can_delete_a_team_and_its_impacts(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        stylesheet = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('data-delete-intervention=', javascript)
        self.assertIn("function deleteIntervention(interventionId)", javascript)
        self.assertIn("window.confirm", javascript)
        self.assertIn("impactedCircleIds", javascript)
        self.assertIn(".intervention-delete", stylesheet)
        self.assertNotIn(".title-block-delete", stylesheet)

    def test_team_codes_are_not_displayed_and_overzone_settings_are_conditional(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("${item.code} —", javascript)
        self.assertNotIn("${intervention?.code || ''}", javascript)
        self.assertIn("Ajouter un surbalisage</label>${overzoneSettings}", javascript)
        self.assertNotIn("Ajouter un surbalisage à chaque impact", javascript)

    def test_box_selection_targets_impact_centers_and_one_company(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        stylesheet = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('data-tool="multiselect"', markup)
        self.assertIn('id="selection-box-layer"', markup)
        self.assertIn("function applyBoxSelection(session)", javascript)
        self.assertIn("circle.cx >= minX", javascript)
        self.assertIn("circle.interventionId === interventionId", javascript)
        self.assertIn("event.shiftKey", javascript)
        self.assertIn("event.altKey", javascript)
        self.assertIn(".impact-selection-box", stylesheet)

    def test_pdf_export_prints_the_visible_sheet_without_substitution(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        stylesheet = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertNotIn('id="print-vector-layer"', markup)
        self.assertNotIn("prepareVectorExport", javascript)
        self.assertNotIn("vector-print-ready", stylesheet)
        self.assertIn("window.print()", javascript)

    def test_export_is_wysiwyg_and_keeps_archive_display_controls(self):
        javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="export-button">Export PDF</button>', markup)
        self.assertIn("window.print()", javascript)
        self.assertNotIn("UNIVERSAL_PDF_DPI", javascript)
        self.assertNotIn("exportVectorPdf", javascript)
        self.assertIn("data-view-archive=", javascript)
        self.assertIn(">Afficher</button>", javascript)
        self.assertIn("archive.has_pdf", javascript)
        self.assertIn("/pdf`), '_blank'", javascript)


if __name__ == "__main__":
    unittest.main()
