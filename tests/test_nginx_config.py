import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class NginxConfigTests(unittest.TestCase):
    def test_api_prefix_is_removed_only_by_proxy_pass(self):
        config = (ROOT / "conf" / "nginx.conf").read_text(encoding="utf-8")

        self.assertNotIn("rewrite ^__PATH__(/.*)$", config)
        self.assertIn("proxy_pass http://127.0.0.1:__PORT__/api/;", config)

    def test_yunohost_authenticated_user_is_forwarded(self):
        config = (ROOT / "conf" / "nginx.conf").read_text(encoding="utf-8")

        self.assertIn("proxy_set_header Remote-User $remote_user;", config)

    def test_pdfjs_uses_standard_javascript_extensions(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")

        self.assertTrue((ROOT / "assets" / "pdfjs" / "pdf.js").is_file())
        self.assertTrue((ROOT / "assets" / "pdfjs" / "pdf.worker.js").is_file())
        self.assertNotIn(".mjs", app)

    def test_frontend_is_revalidated_after_each_upgrade(self):
        nginx = (ROOT / "conf" / "nginx.conf").read_text(encoding="utf-8")
        markup = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertIn('Cache-Control "no-cache, must-revalidate"', nginx)
        self.assertIn('styles.css?v=0.9.10', markup)
        self.assertIn('app.js?v=0.9.10', markup)

    def test_demo_plan_is_not_shipped(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        page = (ROOT / "index.html").read_text(encoding="utf-8")

        self.assertNotIn("mockPlan", app)
        self.assertNotIn('id="mock-plan"', page)
        self.assertNotIn("FOND DE PLAN NORMALISÉ", page)


class SystemdConfigTests(unittest.TestCase):
    def test_data_is_kept_outside_protected_home(self):
        config = (ROOT / "conf" / "systemd.service").read_text(encoding="utf-8")
        manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")

        self.assertIn("ProtectHome=true", config)
        self.assertNotIn("BindPaths=", config)
        self.assertIn("ProtectSystem=strict", config)
        self.assertIn("ReadWritePaths=__DATA_DIR__", config)
        self.assertIn('dir = "/var/lib/__APP__"', manifest)

    def test_package_has_no_cad_conversion_dependencies(self):
        config = (ROOT / "conf" / "systemd.service").read_text(encoding="utf-8")
        manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")
        common = (ROOT / "scripts" / "_common.sh").read_text(encoding="utf-8")
        install = (ROOT / "scripts" / "install").read_text(encoding="utf-8")
        upgrade = (ROOT / "scripts" / "upgrade").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text(encoding="utf-8")

        combined = "\n".join((config, manifest, common, install, workflow)).lower()
        self.assertNotIn("libredwg", combined)
        self.assertNotIn("dwg2dxf", combined)
        self.assertNotIn("ezdxf", combined)
        self.assertNotIn("librsvg", combined)
        self.assertIn('ynh_safe_rm "$install_dir/libredwg"', upgrade)
        self.assertNotIn("install_libredwg", upgrade)


if __name__ == "__main__":
    unittest.main()
