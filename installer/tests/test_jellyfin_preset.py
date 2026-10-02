import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from planner import PlanError, build_plan
from service_bootstrap import (
    OPEN_SUBTITLES_GUID,
    jellyfin_install_opensubtitles,
    jellyfin_update_library_preferences,
)


def host_fixture():
    return {
        "docker": {"installed": True, "compose_installed": True},
        "disks": [{
            "path": "/dev/sdb", "type": "disk", "read_only": False,
            "is_system": False, "filesystem": "ext4",
            "mountpoints": ["/srv/storage"], "children": [],
        }],
        "components": {
            "tailscale": {"installed": False},
            "jellyfin": {"installed": False},
            "qbittorrent": {"installed": False},
        },
    }


def config_fixture():
    return {
        "disk": "/dev/sdb",
        "libraries": ["movies", "series"],
        "services": {
            "tailscale": "skip",
            "jellyfin": "install",
            "qbittorrent": "skip",
        },
        "network": "direct",
        "jellyfin": {
            "metadata_language": "pl",
            "subtitle_language": "en",
            "opensubtitles": True,
        },
    }


class JellyfinPresetTests(unittest.TestCase):
    def test_plan_contains_languages_and_opensubtitles(self):
        plan = build_plan(config_fixture(), host_fixture())
        self.assertEqual(plan["config"]["jellyfin"]["metadata_language"], "pl")
        self.assertEqual(plan["config"]["jellyfin"]["subtitle_language"], "en")
        ids = [a["id"] for a in plan["actions"]]
        self.assertIn("jellyfin.opensubtitles", ids)
        action = next(a for a in plan["actions"] if a["id"] == "jellyfin.libraries")
        self.assertEqual(action["details"]["metadata_language"], "pl")
        self.assertEqual(action["details"]["subtitle_language"], "en")

    def test_opensubtitles_can_be_disabled(self):
        cfg = config_fixture()
        cfg["jellyfin"]["opensubtitles"] = False
        plan = build_plan(cfg, host_fixture())
        self.assertNotIn("jellyfin.opensubtitles", [a["id"] for a in plan["actions"]])

    def test_unknown_jellyfin_language_is_rejected(self):
        cfg = config_fixture()
        cfg["jellyfin"]["subtitle_language"] = "xx"
        with self.assertRaises(PlanError):
            build_plan(cfg, host_fixture())

    @patch("service_bootstrap._jellyfin_json")
    def test_opensubtitles_uses_official_package_guid(self, request):
        jellyfin_install_opensubtitles("http://jf", "TOKEN")
        args, kwargs = request.call_args
        self.assertIn("/Packages/Installed/Open%20Subtitles?", args[1])
        self.assertIn(OPEN_SUBTITLES_GUID, args[1])
        self.assertEqual(kwargs["token"], "TOKEN")

    @patch("service_bootstrap._jellyfin_json")
    def test_library_preferences_preserve_existing_options(self, request):
        original = {"EnableRealtimeMonitor": True, "AutomaticRefreshIntervalDays": 0}
        jellyfin_update_library_preferences(
            "http://jf", "TOKEN", item_id="11111111-1111-1111-1111-111111111111",
            options=original, metadata_language="pl", subtitle_language="en",
        )
        payload = request.call_args.args[2]
        opts = payload["LibraryOptions"]
        self.assertTrue(opts["EnableRealtimeMonitor"])
        self.assertEqual(opts["PreferredMetadataLanguage"], "pl")
        self.assertEqual(opts["SubtitleDownloadLanguages"], ["en"])
        self.assertTrue(opts["SaveSubtitlesWithMedia"])


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]