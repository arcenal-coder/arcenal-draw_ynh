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

    def test_libredwg_is_installed_and_exposed_to_the_service(self):
        config = (ROOT / "conf" / "systemd.service").read_text(encoding="utf-8")
        manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")
        common = (ROOT / "scripts" / "_common.sh").read_text(encoding="utf-8")
        install = (ROOT / "scripts" / "install").read_text(encoding="utf-8")
        upgrade = (ROOT / "scripts" / "upgrade").read_text(encoding="utf-8")

        self.assertIn("libredwg-0.13.3.tar.xz", manifest)
        self.assertIn("83f1f6e78a744777a481ff4520e4cef3f8ac4b2c1c25671077ca12fe81e8816e", manifest)
        self.assertIn("ynh_setup_source", common)
        self.assertIn("test -x \"$install_dir/libredwg/bin/dwg2dxf\"", common)
        self.assertIn("install_libredwg", install)
        self.assertIn("install_libredwg", upgrade)
        self.assertIn("ARCENAL_DWG2DXF=__INSTALL_DIR__/libredwg/bin/dwg2dxf", config)


if __name__ == "__main__":
    unittest.main()
