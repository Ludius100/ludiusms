[Reading 155 lines from start (total: 155 lines, 0 remaining)]

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jobs import JobError, JobStore, InstallJobRunner


def plan_fixture():
    return {
        "schema": 1,
        "config": {},
        "actions": [
            {"id": "one"},
            {"id": "two"},
            {"id": "three"},
        ],
        "destructive": False,
    }


class FakeOps:
    def __init__(self, *, enabled=False):
        self.enabled = enabled
        self.events = []
class JobTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "jobs"
        self.store = JobStore(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_wait_and_resume_same_action(self):
        gate = {"ready": False}
        calls = []

        def executor(action, plan, ops):
            calls.append(action["id"])
            if action["id"] == "two" and not gate["ready"]:
                return {
                    "action_id": "two",
                    "status": "waiting",
                    "interaction": "test",
                }
            return {
                "action_id": action["id"],
                "status": "done",
            }

        runner = InstallJobRunner(
            self.store,
            action_executor=executor,
            ops_factory=FakeOps,
        )
        job = runner.create(plan_fixture())
        paused = runner.run(job["id"], enabled=True)
        self.assertEqual(paused["status"], "waiting")
        self.assertEqual(paused["next_action_index"], 1)
        self.assertEqual(
            [item["action_id"] for item in paused["results"]],
            ["one"],
        )

        gate["ready"] = True
        done = runner.resume(job["id"], enabled=True)

        self.assertEqual(done["status"], "done")
        self.assertEqual(done["next_action_index"], 3)
        self.assertEqual(
            [item["action_id"] for item in done["results"]],
            ["one", "two", "three"],
        )
        self.assertEqual(
            calls,
            ["one", "two", "two", "three"],
        )

    def test_failed_job_retries_current_action(self):
        fail = {"once": True}
        calls = []

        def executor(action, plan, ops):
            calls.append(action["id"])
            if action["id"] == "two" and fail["once"]:
                fail["once"] = False
                raise RuntimeError("boom")
            return {
                "action_id": action["id"],
                "status": "done",
            }
        runner = InstallJobRunner(
            self.store,
            action_executor=executor,
            ops_factory=FakeOps,
        )
        job = runner.create(plan_fixture())

        with self.assertRaises(RuntimeError):
            runner.run(job["id"], enabled=True)

        failed = self.store.load(job["id"])
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["next_action_index"], 1)

        done = runner.retry(job["id"], enabled=True)
        self.assertEqual(done["status"], "done")
        self.assertEqual(
            calls,
            ["one", "two", "two", "three"],
        )

    def test_plan_integrity_tamper_is_detected(self):
        job = self.store.create(plan_fixture())
        path = self.root / f"{job['id']}.json"
        state = json.loads(path.read_text())
        state["plan"]["actions"].append({"id": "evil"})
        path.write_text(json.dumps(state))

        with self.assertRaises(JobError):
            self.store.load(job["id"])

    def test_public_state_does_not_expose_plan(self):
        job = self.store.create(plan_fixture())
        public = self.store.public(job)
        self.assertNotIn("plan", public)
        self.assertNotIn("plan_digest", public)
    def test_destructive_plan_requires_confirmation(self):
        plan = plan_fixture()
        plan["destructive"] = True
        runner = InstallJobRunner(
            self.store,
            action_executor=lambda *args: None,
            ops_factory=FakeOps,
        )
        with self.assertRaises(JobError):
            runner.create(
                plan,
                destructive_confirmed=False,
            )

    def test_state_file_permissions_are_private(self):
        job = self.store.create(plan_fixture())
        path = self.root / f"{job['id']}.json"
        mode = path.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]