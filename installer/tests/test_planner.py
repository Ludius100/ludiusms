import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from planner import PlanError, build_plan


def host_fixture():
    return {
        "docker": {"installed": True, "compose_installed": True},
        "disks": [
            {
                "path": "/dev/sda", "type": "disk", "read_only": False,
                "is_system": True, "filesystem": None, "mountpoints": [],
                "children": [{"path": "/dev/sda1"}],
            },
            {
                "path": "/dev/sdb", "type": "disk", "read_only": False,
                "is_system": False, "filesystem": "ext4",
                "mountpoints": ["/srv/storage"], "children": [],
            },
        ],
        "components": {
            "tailscale": {"installed": True},
            "jellyfin": {"installed": True},
            "qbittorrent": {"installed": True},
        },
    }


def config_fixture():
    return {
        "disk": "/dev/sdb",
        "libraries": ["movies", "series", "anime"],
        "services": {
            "tailscale": "existing",
            "jellyfin": "existing",
            "qbittorrent": "existing",
        },
        "network": "tailscale",
    }
class PlannerTests(unittest.TestCase):
    def test_dashboard_name_is_optional_and_validated(self):
        cfg = config_fixture()
        self.assertEqual(build_plan(cfg,host_fixture())["config"]["display_name"], "")
        cfg["display_name"] = "  Ala  "
        self.assertEqual(build_plan(cfg,host_fixture())["config"]["display_name"], "Ala")
        for name in ("<script>", "A"*41, "Jan\n<script>", 99):
            cfg["display_name"] = name
            with self.subTest(name=name), self.assertRaises(PlanError):
                build_plan(cfg, host_fixture())

    def test_existing_install_is_non_destructive(self):
        plan = build_plan(config_fixture(), host_fixture())
        self.assertFalse(plan["destructive"])
        ids = [item["id"] for item in plan["actions"]]
        self.assertNotIn("storage.format", ids)
        self.assertIn("tailscale.auth", ids)

    def test_system_disk_is_rejected(self):
        cfg = config_fixture()
        cfg["disk"] = "/dev/sda"
        with self.assertRaises(PlanError):
            build_plan(cfg, host_fixture())

    def test_existing_service_cannot_be_reinstalled(self):
        cfg = config_fixture()
        cfg["services"]["jellyfin"] = "install"
        with self.assertRaises(PlanError):
            build_plan(cfg, host_fixture())

    def test_existing_service_credentials_precede_compose_start(self):
        plan = build_plan(config_fixture(), host_fixture())
        ids = [item["id"] for item in plan["actions"]]

        self.assertLess(
            ids.index("qbittorrent.credentials"),
            ids.index("lms.compose"),
        )
        self.assertLess(
            ids.index("jellyfin.credentials"),
            ids.index("lms.compose"),
        )
        self.assertLess(
            ids.index("lms.compose"),
            ids.index("lms.start"),
        )

    def test_tailscale_network_cannot_skip_tailscale(self):
        cfg = config_fixture()
        cfg["services"]["tailscale"] = "skip"
        with self.assertRaises(PlanError):
            build_plan(cfg, host_fixture())
    def test_raw_disk_requires_explicit_destructive_plan(self):
        host = host_fixture()
        host["disks"][1]["filesystem"] = None
        host["disks"][1]["mountpoints"] = []
        plan = build_plan(config_fixture(), host)
        self.assertTrue(plan["destructive"])
        formats = [x for x in plan["actions"] if x["id"] == "storage.format"]
        self.assertEqual(len(formats), 1)
        self.assertTrue(formats[0]["destructive"])

    def test_fresh_services_generate_managed_deployments(self):
        host = host_fixture()
        for component in host["components"].values():
            component["installed"] = False
        cfg = config_fixture()
        cfg["services"] = {
            "tailscale": "install",
            "jellyfin": "install",
            "qbittorrent": "install",
        }
        plan = build_plan(cfg, host)
        ids = [item["id"] for item in plan["actions"]]
        self.assertIn("tailscale.install", ids)
        self.assertIn("lms.compose", ids)
        self.assertIn("lms.start", ids)
        self.assertIn("jellyfin.bootstrap", ids)
        self.assertIn("qbittorrent.bootstrap", ids)
        self.assertNotIn("jellyfin.deploy", ids)
        self.assertNotIn("qbittorrent.deploy", ids)

    def test_anime_maps_to_movies_and_shows(self):
        plan = build_plan(config_fixture(), host_fixture())
        action = next(x for x in plan["actions"] if x["id"] == "jellyfin.libraries")
        self.assertIn(
            {"path": "Anime/Filmy", "content_type": "movies"},
            action["details"]["libraries"],
        )
        self.assertIn(
            {"path": "Anime/Seriale", "content_type": "tvshows"},
            action["details"]["libraries"],
        )

    def test_jellyfin_collection_types_are_api_values(self):
        plan = build_plan(config_fixture(), host_fixture())
        action = next(x for x in plan["actions"] if x["id"] == "jellyfin.libraries")
        values = {item["content_type"] for item in action["details"]["libraries"]}
        self.assertTrue(values.issubset({"movies", "tvshows"}))
        self.assertNotIn("shows", values)


if __name__ == "__main__":
    unittest.main()
