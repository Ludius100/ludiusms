import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frontend_prepare import prepare_custom_js


RAW_JS = """(() => {
    const API = "http://10.0.0.1:8090";
    const WALLPAPER_API = "http://10.0.0.1:8088";

    const SERVICES = {
        jellyfin: { url: "http://10.0.0.1:8096" },
        gdrive: { url: "http://10.0.0.1:8088" }
    };


    function serviceCard(id) {
        return id;
    }

    function renderStaticServiceInfo() {
        return true;
    }


    async function loadData() {
        return true;
    }

    function renderStatus(status) {
        let onlineCount = 0;
        return `${onlineCount} / 4 online`;
    }

    function applyWallpaper() {
        return true;
    }

    function setupActions() {
        const refreshButton =
            document.getElementById(
                "nas-refresh"
            );

        const wallpaperButton =
            document.getElementById(
                "nas-wallpaper"
            );

        const wallpaperInput =
            document.getElementById(
                "wallpaper-input"
            );


        refreshButton.addEventListener(
            "click",
            loadData
        );
    }

    const html = `
        <strong>NAS</strong>
    </div>

    <div class="nas-global-status">
        NAS • Oracle Cloud
    `;
})();
"""


class FrontendPrepareTests(unittest.TestCase):
    def test_prepare_custom_js_is_idempotent(self):
        once = prepare_custom_js(RAW_JS)
        twice = prepare_custom_js(once)

        self.assertEqual(once, twice)
        self.assertIn("const WALLPAPER_API = null;", once)
        self.assertEqual(once.count("const serviceUrl = (port) =>"), 1)
        self.assertEqual(
            once.count("const totalServices = Object.keys(SERVICES).length;"),
            1,
        )

    def test_optional_services_and_private_urls_are_removed(self):
        source = RAW_JS + """\n(() => {
  const URLS = {
    jellyfin: "http://10.0.0.1:8096",
    gdrive: "http://10.0.0.1:8088",
    kuma: "http://10.0.0.1:3001",
    ntfy: "http://10.0.0.1:8089"
  };
  const serviceMeta = [
    ["gdrive", "GDrive", "folder", URLS.gdrive],
    ["jellyfin", "Jellyfin", "play", URLS.jellyfin]
  ];
})();\n"""
        prepared = prepare_custom_js(source)
        self.assertNotIn("10.0.0.1", prepared)
        self.assertNotIn('["gdrive", "GDrive"', prepared)
        self.assertIn("window.location.hostname}:8096", prepared)
        self.assertEqual(prepare_custom_js(prepared), prepared)


if __name__ == "__main__":
    unittest.main()
