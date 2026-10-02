import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from planner import build_plan
from renderer import render_bundle, render_storage_guard


def fresh_host():
    return {
        "docker": {"installed": False, "compose_installed": False},
        "disks": [{
            "path": "/dev/sdb",
            "type": "disk",
            "read_only": False,
            "is_system": False,
            "filesystem": None,
            "mountpoints": [],
            "children": [],
        }],
        "components": {
            "tailscale": {"installed": False},
            "jellyfin": {"installed": False},
            "qbittorrent": {"installed": False},
        },
    }


def fresh_config():
    return {
        "disk": "/dev/sdb",
        "libraries": ["movies", "series", "anime"],
        "services": {
            "tailscale": "install",
            "jellyfin": "install",
            "qbittorrent": "install",
        },
        "network": "tailscale",
    }


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.plan = build_plan(fresh_config(), fresh_host())
        self.bundle = render_bundle(
            self.plan,
            uid=991,
            gid=991,
            bind_address="100.64.0.10",
            allowed_hosts="100.64.0.10:3000",
        )
    def test_bundle_has_split_compose_and_app_env(self):
        self.assertIn(".env", self.bundle)
        self.assertIn("config/lms.env", self.bundle)
        self.assertIn("LMS_BIND_ADDRESS=100.64.0.10", self.bundle[".env"])
        self.assertNotIn("LMS_BIND_ADDRESS", self.bundle["config/lms.env"])

    def test_managed_services_are_rendered(self):
        compose = self.bundle["compose.yaml"]
        for name in ("lms-gateway", "lms-homepage", "lms-api", "lms-jellyfin", "lms-qbittorrent"):
            self.assertIn(name, compose)

    def test_api_uses_internal_container_urls(self):
        env = self.bundle["config/lms.env"]
        self.assertIn("JELLYFIN_URL=http://lms-jellyfin:8096", env)
        self.assertIn("QBITTORRENT_URL=http://lms-qbittorrent:8080", env)

    def test_anime_paths_are_split(self):
        env = self.bundle["config/lms.env"]
        self.assertIn("LIBRARY_ANIME_PATH=/nas/Anime/Seriale", env)
        self.assertIn("LIBRARY_ANIME_MOVIES_PATH=/nas/Anime/Filmy", env)

    def test_gateway_proxies_api(self):
        caddy = self.bundle["gateway/Caddyfile"]
        self.assertIn("handle @lms_api", caddy)
        self.assertIn("/api/jellyfin /api/jellyfin/*", caddy)
        self.assertIn("reverse_proxy lms-api:8090", caddy)
        self.assertIn("reverse_proxy lms-homepage:3000", caddy)
        self.assertNotIn("handle /api/*", caddy)
    def test_no_current_server_identifiers_leak(self):
        all_text = "\n".join(self.bundle.values())
        self.assertNotIn("100.127.67.28", all_text)
        self.assertNotIn("nas-server", all_text)
        self.assertNotIn("ocid1.", all_text)

    def test_qbittorrent_ports_follow_selected_bind(self):
        compose = self.bundle["compose.yaml"]
        self.assertIn('${LMS_BIND_ADDRESS}:8080:8080/tcp', compose)
        self.assertIn('${LMS_BIND_ADDRESS}:6881:6881/tcp', compose)
        self.assertIn('${LMS_BIND_ADDRESS}:6881:6881/udp', compose)
        self.assertNotIn('      - "6881:6881/tcp"', compose)

    def test_nas_containers_do_not_autostart_before_disk_mount(self):
        compose = self.bundle["compose.yaml"]
        for service in ("dashboard-api", "jellyfin", "qbittorrent"):
            section = compose.split("  " + service + ":", 1)[1].split("\n\n", 1)[0]
            self.assertIn("restart: on-failure:5", section)
            self.assertNotIn("restart: unless-stopped", section)
        # Brama i Homepage nie montują NAS, więc mogą wystartować normalnie.
        self.assertIn("restart: unless-stopped", compose)

    def test_reboot_guard_waits_for_mount_and_recreates_managed_containers(self):
        unit = render_storage_guard(self.plan)
        self.assertIn("RequiresMountsFor=/srv/lms-media", unit)
        self.assertIn("ConditionPathIsMountPoint=/srv/lms-media", unit)
        self.assertIn("ExecStartPre=/usr/bin/findmnt --mountpoint /srv/lms-media", unit)
        self.assertIn("--force-recreate dashboard-api jellyfin qbittorrent", unit)
        self.assertNotIn("down", unit)
        self.assertNotIn("--volumes", unit)

    def test_existing_services_are_not_redeployed(self):
        host = fresh_host()
        host["disks"][0]["filesystem"] = "ext4"
        host["disks"][0]["mountpoints"] = ["/srv/media"]
        for component in host["components"].values():
            component["installed"] = True

        cfg = fresh_config()
        cfg["services"] = {
            "tailscale": "existing",
            "jellyfin": "existing",
            "qbittorrent": "existing",
        }
        plan = build_plan(cfg, host)
        bundle = render_bundle(
            plan,
            uid=991,
            gid=991,
            bind_address="127.0.0.1",
            allowed_hosts="localhost:3000",
        )
        compose = bundle["compose.yaml"]
        env = bundle["config/lms.env"]
        self.assertNotIn("container_name: lms-jellyfin", compose)
        self.assertNotIn("container_name: lms-qbittorrent", compose)
        self.assertIn("JELLYFIN_URL=http://host.docker.internal:8096", env)
        self.assertIn("QBITTORRENT_URL=http://host.docker.internal:8080", env)
        self.assertIn("LMS_MEDIA_ROOT=/srv/media/LMS", bundle[".env"])


if __name__ == "__main__":
    unittest.main()
