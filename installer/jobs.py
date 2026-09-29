[Reading 247 lines from start (total: 247 lines, 0 remaining)]

#!/usr/bin/env python3
import hashlib
import json
import os
import uuid
from copy import deepcopy
from pathlib import Path

from host_ops import HostOps


class JobError(RuntimeError):
    pass


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def plan_digest(plan):
    payload = _canonical_json(plan).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
class JobStore:
    def __init__(self, root):
        self.root = Path(root)

    def _path(self, job_id):
        if not isinstance(job_id, str) or not job_id:
            raise JobError("Nieprawidłowy identyfikator zadania.")
        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_-"
        )
        if any(ch not in allowed for ch in job_id):
            raise JobError("Nieprawidłowy identyfikator zadania.")
        return self.root / f"{job_id}.json"

    def _ensure_root(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)

    def create(self, plan, *, destructive_confirmed=False):
        self._ensure_root()
        job_id = uuid.uuid4().hex
        state = {
            "schema": 1,
            "id": job_id,
            "plan": deepcopy(plan),
            "plan_digest": plan_digest(plan),
            "next_action_index": 0,
            "status": "queued",
            "waiting_for": None,
            "results": [],
            "destructive_confirmed": bool(
                destructive_confirmed
            ),
            "error": None,
        }
        self.save(state)
        return state

    def load(self, job_id):
        path = self._path(job_id)
        try:
            state = json.loads(
                path.read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise JobError(
                "Nie znaleziono zadania instalacji."
            ) from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise JobError(
                "Nie udało się odczytać stanu instalacji."
            ) from exc

        if state.get("id") != job_id:
            raise JobError(
                "Stan zadania ma nieprawidłowy identyfikator."
            )
        if plan_digest(state.get("plan")) != state.get(
            "plan_digest"
        ):
            raise JobError(
                "Plan zadania nie przeszedł kontroli integralności."
            )
        return state

    def save(self, state):
        self._ensure_root()
        path = self._path(state.get("id"))
        tmp = path.with_name(path.name + ".tmp")
        payload = json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        tmp.write_text(payload, encoding="utf-8")
        tmp.chmod(0o600)
        os.replace(tmp, path)
        path.chmod(0o600)
        return state

    def public(self, state):
        return {
            "id": state["id"],
            "status": state["status"],
            "next_action_index": state[
                "next_action_index"
            ],
            "action_count": len(
                state["plan"].get("actions", [])
            ),
            "waiting_for": deepcopy(
                state.get("waiting_for")
            ),
            "results": deepcopy(
                state.get("results", [])
            ),
            "error": state.get("error"),
        }


class InstallJobRunner:
    def __init__(
        self,
        store,
        *,
        action_executor,
        ops_factory=HostOps,
    ):
        self.store = store
        self.action_executor = action_executor
        self.ops_factory = ops_factory

    def create(
        self,
        plan,
        *,
        destructive_confirmed=False,
    ):
        if (
            plan.get("destructive")
            and not destructive_confirmed
        ):
            raise JobError(
                "Plan destrukcyjny wymaga "
                "osobnego potwierdzenia."
            )
        return self.store.create(
            plan,
            destructive_confirmed=destructive_confirmed,
        )

    def run(self, job_id, *, enabled):
        state = self.store.load(job_id)

        if state["status"] == "done":
            return state
        if state["status"] == "failed":
            raise JobError(
                "Zadanie zakończyło się błędem. "
                "Użyj jawnego ponowienia."
            )
        if state["status"] == "waiting":
            return state

        plan = state["plan"]
        actions = plan.get("actions") or []
        index = int(
            state.get("next_action_index", 0)
        )
        ops = self.ops_factory(enabled=enabled)

        state["status"] = "running"
        state["error"] = None
        self.store.save(state)

        try:
            while index < len(actions):
                action = actions[index]
                result = self.action_executor(
                    action,
                    plan,
                    ops,
                )

                if result.get("status") == "waiting":
                    state["status"] = "waiting"
                    state["waiting_for"] = deepcopy(result)
                    state["next_action_index"] = index
                    self.store.save(state)
                    return state

                if enabled and result.get("status") == "planned":
                    raise JobError(
                        f"Akcja {action.get('id')} nie ma jeszcze implementacji wykonawczej."
                    )

                state["results"].append(
                    deepcopy(result)
                )
                index += 1
                state["next_action_index"] = index
                state["waiting_for"] = None
                self.store.save(state)

            state["status"] = "done"
            state["waiting_for"] = None
            state["next_action_index"] = len(actions)
            self.store.save(state)
            return state

        except Exception as exc:
            state["status"] = "failed"
            state["error"] = str(exc)
            state["waiting_for"] = None
            self.store.save(state)
            raise
    def resume(self, job_id, *, enabled):
        state = self.store.load(job_id)
        if state["status"] != "waiting":
            raise JobError(
                "Zadanie nie oczekuje na interakcję."
            )
        state["status"] = "queued"
        state["waiting_for"] = None
        self.store.save(state)
        return self.run(job_id, enabled=enabled)

    def retry(self, job_id, *, enabled):
        state = self.store.load(job_id)
        if state["status"] != "failed":
            raise JobError(
                "Ponowienie jest dostępne tylko po błędzie."
            )
        state["status"] = "queued"
        state["error"] = None
        self.store.save(state)
        return self.run(job_id, enabled=enabled)

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]