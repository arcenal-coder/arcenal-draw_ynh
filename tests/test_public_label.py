import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PublicLabelTests(unittest.TestCase):
    def test_label_updates_settings_and_portal_without_changing_permissions(self):
        result = subprocess.run(
            ["bash", "-c", '''
set -eu
source "$1/scripts/_common.sh"
ynh_app_setting_set() { printf 'setting'; printf ' <%s>' "$@"; printf '\\n'; }
yunohost() { printf 'yunohost'; printf ' <%s>' "$@"; printf '\\n'; }
sync_public_label
''', "test", str(ROOT)],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(result.stdout.splitlines(), [
            "setting <--key=label> <--value=Crobard>",
            "yunohost <user> <permission> <update> <arcenal_draw.main> <--label=Crobard>",
        ])

    def test_label_update_failure_is_not_hidden(self):
        result = subprocess.run(
            ["bash", "-c", '''
set -eu
source "$1/scripts/_common.sh"
ynh_app_setting_set() { return 1; }
yunohost() { exit 99; }
sync_public_label
''', "test", str(ROOT)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
