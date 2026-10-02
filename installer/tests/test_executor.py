import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from executor import ExecutionError, _storage_format, _verify_storage_mount, _lms_health, _lms_start, execute_plan
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

    def test_format_refuses_changed_disk_state(self):
        for kind, expected in (
            ("partition", "partycje"),
            ("filesystem", "system plików"),
            ("mounted", "zamontowane"),
        ):
            with self.subTest(kind=kind):
                runner = Mock(enabled=True, events=[])
                def output(argv, timeout=10):
                    key = tuple(argv[1:4])
                    if key == ("-dn", "-o", "TYPE"):
                        return "disk"
                    if key == ("-nr", "-o", "TYPE"):
                        return "disk" + chr(10) + "part" if kind == "partition" else "disk"
                    if key == ("-dn", "-o", "FSTYPE"):
                        return "ext4" if kind == "filesystem" else ""
                    if key == ("-nr", "-o", "MOUNTPOINTS"):
                        return "/srv/data" if kind == "mounted" else ""
                    return ""
                with patch("executor._output", side_effect=output):
                    with self.assertRaisesRegex(ExecutionError, expected):
                        _storage_format(
                            {"id": "storage.format", "details": {"disk": "/dev/sdb"}},
                            {}, runner,
                        )
                runner.run.assert_not_called()

    def test_start_refuses_unmounted_disk_before_starting_docker(self):
        plan = {"config": {"disk": "/dev/sdb", "storage": {
            "mountpoint": "/srv/lms-media", "media_root": "/srv/lms-media"}}}
        runner = Mock(enabled=True, events=[])
        with patch("executor._output", return_value=""):
            with self.assertRaisesRegex(ExecutionError, "nie jest zamontowany"):
                _lms_start({"id": "lms.start"}, plan, runner)
        runner.run.assert_not_called()

    def test_start_refuses_other_disk_mounted_at_nas(self):
        plan = {"config": {"disk": "/dev/sdb", "storage": {
            "mountpoint": "/srv/lms-media", "media_root": "/srv/lms-media"}}}
        runner = Mock(enabled=True, events=[])
        with patch("executor._output", return_value="/dev/sda"), \
             patch("executor.os.path.samefile", return_value=False):
            with self.assertRaisesRegex(ExecutionError, "inny dysk"):
                _lms_start({"id": "lms.start"}, plan, runner)
        runner.run.assert_not_called()

    def test_health_detects_stale_qbittorrent_mount(self):
        plan = {"config": {"services": {"qbittorrent": "install", "jellyfin": "skip"}},
                "actions": [{"id": "libraries.create", "details": {"paths": ["Filmy"]}}]}
        runner = Mock(enabled=True, events=[])
        with patch("executor._output", return_value="true"), \
             patch("executor._service_identity", return_value=(999, 987)), \
             patch("executor._command_ok", side_effect=lambda argv: argv[4] != "lms-qbittorrent"):
            with self.assertRaisesRegex(ExecutionError, "nie widzi biblioteki"):
                _lms_health({"id": "lms.health"}, plan, runner)

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
