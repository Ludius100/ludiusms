import json
import os
import subprocess
import sys
import unittest

from app import create_app
from config import HOMEPAGE_ORIGIN


EXPECTED_ROUTES = {
    "/api/activity": {"GET", "OPTIONS"},
    "/api/health": {"GET", "OPTIONS"},
    "/api/jellyfin": {"GET", "OPTIONS"},
    "/api/media/last-episode": {"GET", "OPTIONS"},
    "/api/media/plan": {"POST", "OPTIONS"},
    "/api/media/titles": {"GET", "OPTIONS"},
    "/api/media/upload": {"POST", "OPTIONS"},
    "/api/media/upload/<upload_id>": {"GET", "DELETE", "OPTIONS"},
    "/api/media/upload/<upload_id>/chunk": {"POST", "OPTIONS"},
    "/api/media/upload/<upload_id>/finalize": {"POST", "OPTIONS"},
    "/api/media/upload/init": {"POST", "OPTIONS"},
    "/api/modules": {"GET", "OPTIONS"},
    "/api/qbittorrent": {"GET", "OPTIONS"},
    "/api/qbittorrent/add": {"POST", "OPTIONS"},
    "/api/qbittorrent/libraries": {"GET", "OPTIONS"},
    "/api/qbittorrent/start": {"POST", "OPTIONS"},
    "/api/status": {"GET", "OPTIONS"},
    "/api/system": {"GET", "OPTIONS"},
}


def api_routes(app):
    routes = {}

    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/"):
            continue

        routes.setdefault(rule.rule, set()).update(
            rule.methods - {"HEAD"}
        )

    return routes


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(start_collectors=False)
        self.client = self.app.test_client()

    def test_route_contract(self):
        self.assertEqual(
            api_routes(self.app),
            EXPECTED_ROUTES,
        )

    def test_health_and_cors(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "ok"},
        )
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            HOMEPAGE_ORIGIN,
        )
        self.assertEqual(
            response.headers["Cache-Control"],
            "no-store",
        )

    def test_module_manifest(self):
        response = self.client.get("/api/modules")

        self.assertEqual(response.status_code, 200)
        modules = response.get_json()["modules"]

        self.assertIn("jellyfin", modules)
        self.assertIn("qbittorrent", modules)
        self.assertTrue(modules["jellyfin"]["enabled"])
        self.assertTrue(modules["qbittorrent"]["enabled"])

    def test_disabled_modules_are_not_registered(self):
        script = """
import json
import sys
from app import create_app

app = create_app()
paths = sorted({
    rule.rule
    for rule in app.url_map.iter_rules()
    if rule.rule.startswith("/api/")
})

print(json.dumps({
    "paths": paths,
    "jellyfinImported": "routes.jellyfin" in sys.modules,
    "qbImported": "routes.qbittorrent" in sys.modules,
    "collectorImported": "services.jellyfin_activity" in sys.modules,
}))
"""

        env = os.environ.copy()
        env["ENABLE_JELLYFIN"] = "false"
        env["ENABLE_QBITTORRENT"] = "false"
        env["GDRIVE_URL"] = ""
        env["KUMA_URL"] = ""
        env["NTFY_URL"] = ""

        result = subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            cwd="/app",
            check=True,
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)
        self.assertNotIn("/api/jellyfin", data["paths"])
        self.assertNotIn("/api/qbittorrent", data["paths"])
        self.assertFalse(data["jellyfinImported"])
        self.assertFalse(data["qbImported"])
        self.assertFalse(data["collectorImported"])


if __name__ == "__main__":
    unittest.main()
