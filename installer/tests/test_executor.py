[Reading 96 lines from start (total: 96 lines, 0 remaining)]

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from executor import ExecutionError, execute_plan
from planner import build_plan


def plan_fixture(destructive=False):
    actions = [
        {
            "id": "lms.health",
            "phase": "verify",
            "title": "Health",
            "destructive": False,
            "interaction": False,
            "details": {},
        }
    ]
    if destructive:
        actions.insert(0, {
            "id": "storage.format",
            "phase": "storage",
            "title": "Format",
            "destructive": True,
            "interaction": False,
            "details": {"disk": "/dev/sdz"},
        })
    return {
        "schema": 1,
        "config": {},
        "actions": actions,
        "destructive": destructive,
        "requires_interaction": False,
    }
class ExecutorTests(unittest.TestCase):
    def test_preview_does_not_execute_commands(self):
        result = execute_plan(plan_fixture(), enabled=False)
        self.assertFalse(result["executed"])
        self.assertEqual(result["results"][0]["status"], "planned")

    def test_destructive_preview_requires_confirmation(self):
        with self.assertRaises(ExecutionError):
            execute_plan(
                plan_fixture(destructive=True),
                enabled=False,
                destructive_confirmed=False,
            )

    def test_execution_is_globally_fused_off(self):
        with self.assertRaises(ExecutionError):
            execute_plan(plan_fixture(), enabled=True)

    def test_full_fresh_plan_can_be_previewed_end_to_end(self):
        host = {
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
        config = {
            "disk": "/dev/sdb",
            "libraries": ["movies", "series", "anime"],
            "services": {
                "tailscale": "install",
                "jellyfin": "install",
                "qbittorrent": "install",
            },
            "network": "tailscale",
        }
        plan = build_plan(config, host)
        result = execute_plan(
            plan,
            enabled=False,
            destructive_confirmed=True,
        )
        self.assertFalse(result["executed"])
        self.assertEqual(len(result["results"]), len(plan["actions"]))


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]