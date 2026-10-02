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


class SystemdConfigTests(unittest.TestCase):
    def test_data_is_kept_outside_protected_home(self):
        config = (ROOT / "conf" / "systemd.service").read_text(encoding="utf-8")
        manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")

        self.assertIn("ProtectHome=true", config)
        self.assertNotIn("BindPaths=", config)
        self.assertIn("ProtectSystem=strict", config)
        self.assertIn("ReadWritePaths=__DATA_DIR__", config)
        self.assertIn('dir = "/var/lib/__APP__"', manifest)


if __name__ == "__main__":
    unittest.main()
