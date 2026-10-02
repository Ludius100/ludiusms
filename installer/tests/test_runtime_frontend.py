"""Regression: the runtime must contain the built custom dashboard, not assets alone."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from executor import _lms_compose
from host_ops import HostOps
from test_frontend_prepare import RAW_JS


class RuntimeFrontendTests(unittest.TestCase):
    def test_compose_action_installs_custom_js_css_and_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            api = source / "dashboard-api"
            homepage = source / "homepage"
            api.mkdir(parents=True)
            homepage.mkdir(parents=True)
            for filename in ("Dockerfile", "app.py", "config.py", "gunicorn.conf.py"):
                (api / filename).write_text("# test fixture\n", encoding="utf-8")
            for directory in ("services", "routes", "modules"):
                (api / directory).mkdir()
            (homepage / "custom.js").write_text(RAW_JS, encoding="utf-8")
            (homepage / "custom.css").write_text("body{}", encoding="utf-8")
            (homepage / "assets").mkdir()
            for filename in ("lms-logo.webp", "lms-hero.webp"):
                (homepage / "assets" / filename).write_bytes(b"fixture")
            install = root / "runtime"
            plan = {"config": {
                "storage": {"media_root": "/srv/lms-media"},
                "display_name": "Ala",
                "network": "direct", "libraries": [],
                "services": {"jellyfin": "skip", "qbittorrent": "skip"},
            }}
            runner = HostOps(enabled=True)
            with patch("executor.SOURCE_ROOT", source), \
                 patch("executor.INSTALL_ROOT", install), \
                 patch("executor._service_identity", return_value=(os.getuid(), os.getgid())), \
                 patch("executor._homepage_allowed_hosts", return_value="localhost:3000"):
                _lms_compose({"id": "lms.compose"}, plan, runner)
            config = install / "homepage" / "config"
            self.assertIn("const WALLPAPER_API = null", (config / "custom.js").read_text())
            self.assertEqual((config / "custom.css").read_text(), "body{}")
            self.assertEqual((install / "homepage" / "assets" / "lms-hero.webp").read_bytes(), b"fixture")
            self.assertEqual(config.stat().st_mode & 0o777, 0o750)
            self.assertEqual((install / "homepage" / "assets" / "lms-profile.json").read_text().strip(), '{"displayName": "Ala"}')

if __name__ == "__main__": unittest.main()
