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

        self.assertIn('more_set_headers "Cache-Control: no-cache, must-revalidate"', nginx)
        self.assertIn('styles.css?v=0.9.16', markup)
        self.assertIn('app.js?v=0.9.16', markup)

    def test_frontend_has_restrictive_security_headers(self):
        nginx = (ROOT / "conf" / "nginx.conf").read_text(encoding="utf-8")

        self.assertIn("Content-Security-Policy", nginx)
        self.assertIn("object-src 'none'", nginx)
        self.assertIn("frame-ancestors 'self'", nginx)
        self.assertIn('more_set_headers "X-Content-Type-Options: nosniff"', nginx)
        self.assertIn('more_set_headers "X-Frame-Options: SAMEORIGIN"', nginx)

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
        self.assertIn('default = "all_users"', manifest)
        for directive in (
            "NoNewPrivileges=true",
            "DevicePolicy=closed",
            "LockPersonality=true",
            "PrivateDevices=true",
            "ProtectKernelModules=true",
            "ProtectKernelTunables=true",
            "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6",
            "RestrictNamespaces=true",
            "RestrictRealtime=true",
            "RestrictSUIDSGID=true",
            "SystemCallArchitectures=native",
            "UMask=0027",
        ):
            self.assertIn(directive, config)

    def test_upgrade_only_removes_replaced_application_directories(self):
        upgrade = (ROOT / "scripts" / "upgrade").read_text(encoding="utf-8")

        self.assertIn('ynh_safe_rm "$install_dir/web/assets"', upgrade)
        self.assertIn('ynh_safe_rm "$install_dir/backend"', upgrade)
        self.assertEqual(upgrade.count("ynh_safe_rm"), 2)


if __name__ == "__main__":
    unittest.main()
