#!/usr/bin/env python3
import argparse
import json
import os
import platform
import secrets
import shutil
import subprocess
import urllib.request
from copy import deepcopy
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from executor import (
    EXECUTION_READY,
    INSTALL_ROOT,
    ExecutionError,
    ensure_execution_runtime,
    execute_action,
    execute_plan,
    service_base_url,
)
from final_credentials import (
    FinalCredentialsError,
    collect_managed_credentials,
)
from interaction_inputs import (
    InteractionInputError,
    save_existing_jellyfin_credentials,
    save_existing_qbittorrent_credentials,
)
from job_manager import JobManager, JobManagerError
from jobs import JobError, JobStore, InstallJobRunner
from planner import PlanError, build_plan

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"

# Development safety: the current setup build is discovery/planning only.
# Real system-changing actions will be enabled only in a dedicated test build.
SETUP_MODE = os.environ.get("LMS_SETUP_MODE", "plan").strip().lower()
CHANGES_ALLOWED = False
EXECUTION_BLOCK_REASON = "Tryb planowania"
SETUP_TOKEN = os.environ.get("LMS_SETUP_TOKEN") or secrets.token_urlsafe(24)
MAX_JSON_BODY = 64 * 1024

JOB_ROOT = Path(
    os.environ.get(
        "LMS_JOB_ROOT",
        "/var/lib/lms-installer/jobs",
    )
)
JOB_STORE = JobStore(JOB_ROOT)
JOB_RUNNER = InstallJobRunner(
    JOB_STORE,
    action_executor=execute_action,
)
JOB_MANAGER = JobManager(JOB_RUNNER)

def run(cmd, timeout=3):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)

def exists(name):
    return shutil.which(name) is not None

def service_state(name):
    rc, out, _ = run(["systemctl", "is-active", name], 2)
    return out == "active" if rc in (0, 3) else False
def read_os():
    data = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value.strip().strip('"')
    except OSError:
        pass
    return {
        "name": data.get("PRETTY_NAME", platform.platform()),
        "id": data.get("ID", "unknown"),
        "version": data.get("VERSION_ID", ""),
        "arch": platform.machine(),
        "kernel": platform.release(),
    }

def memory_info():
    total_kib = 0
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                total_kib = int(line.split()[1])
                break
    except (OSError, ValueError):
        pass
    return {"total_bytes": total_kib * 1024}

def cpu_info():
    return {"logical_cores": os.cpu_count() or 0, "model": platform.processor() or platform.machine()}
def docker_info():
    installed = exists("docker")
    compose = False
    version = None
    compose_version = None
    usable = False
    if installed:
        rc, out, _ = run(["docker", "--version"])
        version = out if rc == 0 else None
        rc, out, _ = run(["docker", "compose", "version"])
        compose = rc == 0
        compose_version = out if compose else None
        rc, _, _ = run(["docker", "info"], 5)
        usable = rc == 0
    return {
        "installed": installed,
        "usable": usable,
        "version": version,
        "compose_installed": compose,
        "compose_version": compose_version,
    }

def disks_info():
    rc, out, _ = run([
        "lsblk", "-J", "-b", "-o",
        "NAME,PATH,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL,TRAN,RO"
    ], 3)
    if rc != 0 or not out:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    rc, root_source, _ = run(["findmnt", "-n", "-o", "SOURCE", "/"], 2)
    root_source = root_source if rc == 0 else ""

    def convert(node):
        path = node.get("path") or ""
        children = [convert(x) for x in node.get("children") or []]
        is_system = bool(root_source and (root_source.startswith(path) or path.startswith(root_source)))
        if any(child["is_system"] for child in children):
            is_system = True
        return {
            "name": node.get("name"),
            "path": path,
            "size_bytes": node.get("size") or 0,
            "type": node.get("type"),
            "filesystem": node.get("fstype"),
            "mountpoints": [x for x in (node.get("mountpoints") or []) if x],
            "model": (node.get("model") or "").strip(),
            "transport": node.get("tran"),
            "read_only": bool(node.get("ro")),
            "is_system": is_system,
            "children": children,
        }

    return [convert(x) for x in data.get("blockdevices", [])]

def optional_component(command, service=None):
    installed = exists(command)
    return {"installed": installed, "running": service_state(service) if installed and service else None}
def existing_lms_installation():
    if not exists("docker"):
        return False
    rc, out, _ = run(["docker", "ps", "-a", "--format", "{{.Names}}"], 4)
    if rc != 0:
        return False
    names = set(out.splitlines())
    return "dashboard-api" in names and "homepage" in names


def qbittorrent_info():
    installed = exists("qbittorrent-nox") or exists("qbittorrent")
    running = service_state("qbittorrent-nox") or service_state("qbittorrent")
    container = False
    if exists("docker"):
        rc, out, _ = run(["docker", "ps", "--format", "{{.Names}}"], 3)
        container = rc == 0 and "qbittorrent" in out.splitlines()
    return {"installed": installed or container, "running": running or container, "container": container}

def oracle_info():
    req = urllib.request.Request(
        "http://169.254.169.254/opc/v2/instance/",
        headers={"Authorization": "Bearer Oracle"},
    )
    try:
        with urllib.request.urlopen(req, timeout=0.7) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"detected": False}

    # Whitelist only non-secret fields needed by the setup UI.
    return {
        "detected": True,
        "region": raw.get("region"),
        "shape": raw.get("shape"),
    }

def execution_gate_error():
    if existing_lms_installation():
        return (
            "Wykryto istniejącą instalację LMS. "
            "Tryb wykonawczy jest zablokowany."
        )
    if not CHANGES_ALLOWED:
        return (
            EXECUTION_BLOCK_REASON
            or "Zmiany systemowe są zablokowane."
        )
    if not EXECUTION_READY:
        return (
            "Silnik wykonawczy nie jest jeszcze "
            "gotowy do testów."
        )
    try:
        ensure_execution_runtime()
    except ExecutionError as exc:
        return str(exc)
    return None


def detect():
    return {
        "schema": 1,
        "installer": {
            "mode": SETUP_MODE,
            "changes_allowed": CHANGES_ALLOWED,
            "execution_ready": EXECUTION_READY,
            "block_reason": EXECUTION_BLOCK_REASON,
            "existing_lms_detected": existing_lms_installation(),
        },
        "os": read_os(),
        "cpu": cpu_info(),
        "memory": memory_info(),
        "docker": docker_info(),
        "disks": disks_info(),
        "components": {
            "tailscale": optional_component("tailscale", "tailscaled"),
            "jellyfin": optional_component("jellyfin", "jellyfin"),
            "qbittorrent": qbittorrent_info(),
        },
        "cloud": {"oracle": oracle_info()},
    }
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print("[setup-web]", fmt % args)

    def authorized(self):
        supplied = self.headers.get("X-LMS-Setup-Token", "")
        return secrets.compare_digest(supplied, SETUP_TOKEN)

    def require_authorized(self):
        if self.authorized():
            return True
        self.send_json({"ok": False, "error": "unauthorized"}, status=403)
        return False

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            return self.send_json({
                "ok": True,
                "service": "lms-setup",
                "mode": SETUP_MODE,
                "changes_allowed": CHANGES_ALLOWED,
                "execution_ready": EXECUTION_READY,
                "block_reason": EXECUTION_BLOCK_REASON,
            })
        if path == "/api/detect":
            if not self.require_authorized():
                return
            return self.send_json(detect())

        if path.startswith("/api/jobs/"):
            if not self.require_authorized():
                return
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[3] == "credentials":
                return self.handle_job_credentials(parts[2])
            if len(parts) == 3:
                return self.handle_job_status(parts[2])

        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if not self.require_authorized():
            return
        if path == "/api/plan":
            return self.handle_plan()
        if path == "/api/execute":
            return self.handle_execute()
        if path == "/api/jobs/start":
            return self.handle_job_start()
        if path.startswith("/api/jobs/"):
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[3] in {"resume", "retry"}:
                return self.handle_job_transition(
                    parts[2],
                    parts[3],
                )
            if len(parts) == 4 and parts[3] == "input":
                return self.handle_job_input(parts[2])
        return self.send_json({"ok": False, "error": "not_found"}, status=404)

    def read_json(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise PlanError("Nieprawidłowa długość żądania.")
        if size <= 0 or size > MAX_JSON_BODY:
            raise PlanError("Nieprawidłowy rozmiar żądania.")
        raw = self.rfile.read(size)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise PlanError("Nieprawidłowy JSON.")

    def handle_plan(self):
        try:
            payload = self.read_json()
            plan = build_plan(payload, detect())
        except PlanError as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=400,
            )
        public_plan = deepcopy(plan)
        public_plan["config"].pop("qbittorrent_password", None)
        return self.send_json({"ok": True, "plan": public_plan})

    def handle_job_credentials(self, job_id):
        try:
            state = JOB_STORE.load(job_id)
            if state.get("status") != "done":
                raise JobError(
                    "Dane logowania są dostępne dopiero po zakończeniu instalacji."
                )
            credentials = collect_managed_credentials(
                state["plan"],
                INSTALL_ROOT,
            )
        except JobError as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=409,
            )
        except FinalCredentialsError as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=500,
            )

        return self.send_json({
            "ok": True,
            "credentials": credentials,
        })

    def handle_job_status(self, job_id):
        try:
            state = JOB_STORE.load(job_id)
        except JobError as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=404,
            )
        return self.send_json({
            "ok": True,
            "job": JOB_STORE.public(state),
            "active": JOB_MANAGER.is_active(job_id),
        })

    def handle_job_start(self):
        try:
            payload = self.read_json()
            selection = payload.get("config")
            destructive_confirmed = (
                payload.get("confirm_destructive") is True
            )
            plan = build_plan(selection, detect())
        except PlanError as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=400,
            )

        blocked = execution_gate_error()
        if blocked:
            return self.send_json(
                {"ok": False, "error": blocked},
                status=409,
            )

        try:
            state = JOB_RUNNER.create(
                plan,
                destructive_confirmed=destructive_confirmed,
            )
            JOB_MANAGER.start(
                state["id"],
                mode="run",
                enabled=True,
            )
        except (JobError, JobManagerError) as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=409,
            )

        return self.send_json(
            {
                "ok": True,
                "job": JOB_STORE.public(state),
            },
            status=202,
        )

    def handle_job_input(self, job_id):
        blocked = execution_gate_error()
        if blocked:
            return self.send_json(
                {"ok": False, "error": blocked},
                status=409,
            )

        try:
            state = JOB_STORE.load(job_id)
            if JOB_MANAGER.is_active(job_id):
                raise JobManagerError(
                    "To zadanie jest już wykonywane."
                )
            if state.get("status") != "waiting":
                raise JobError(
                    "Zadanie nie oczekuje na dane użytkownika."
                )

            waiting = state.get("waiting_for") or {}
            interaction = waiting.get("interaction")
            payload = self.read_json()
            plan = state["plan"]

            if interaction == "qbittorrent-credentials":
                save_existing_qbittorrent_credentials(
                    base_url=service_base_url(
                        plan,
                        8080,
                        enabled=True,
                    ),
                    username=payload.get("username"),
                    password=payload.get("password"),
                    secret_path=(
                        INSTALL_ROOT
                        / "secrets"
                        / "qbittorrent.env"
                    ),
                )
            elif interaction == "jellyfin-credentials":
                save_existing_jellyfin_credentials(
                    base_url=service_base_url(
                        plan,
                        8096,
                        enabled=True,
                    ),
                    username=payload.get("username"),
                    password=payload.get("password"),
                    token_path=(
                        INSTALL_ROOT
                        / "secrets"
                        / "jellyfin_api_key"
                    ),
                )
            else:
                raise JobError(
                    "Ten krok nie przyjmuje danych logowania."
                )

            JOB_MANAGER.start(
                job_id,
                mode="resume",
                enabled=True,
            )
        except (
            JobError,
            JobManagerError,
            InteractionInputError,
            PlanError,
        ) as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=409,
            )

        return self.send_json(
            {
                "ok": True,
                "job": JOB_STORE.public(state),
            },
            status=202,
        )

    def handle_job_transition(self, job_id, mode):
        blocked = execution_gate_error()
        if blocked:
            return self.send_json(
                {"ok": False, "error": blocked},
                status=409,
            )

        try:
            state = JOB_STORE.load(job_id)
            if JOB_MANAGER.is_active(job_id):
                raise JobManagerError(
                    "To zadanie jest już wykonywane."
                )

            if mode == "resume":
                if state["status"] != "waiting":
                    raise JobError(
                        "Zadanie nie oczekuje na interakcję."
                    )
            elif mode == "retry":
                if state["status"] != "failed":
                    raise JobError(
                        "Ponowienie jest dostępne tylko po błędzie."
                    )

            JOB_MANAGER.start(
                job_id,
                mode=mode,
                enabled=True,
            )
        except (JobError, JobManagerError) as exc:
            return self.send_json(
                {"ok": False, "error": str(exc)},
                status=409,
            )

        return self.send_json(
            {
                "ok": True,
                "job": JOB_STORE.public(state),
            },
            status=202,
        )

    def handle_execute(self):
        try:
            payload = self.read_json()
            selection = payload.get("config")
            destructive_confirmed = payload.get("confirm_destructive") is True
            host = detect()
            plan = build_plan(selection, host)
        except PlanError as exc:
            return self.send_json({"ok": False, "error": str(exc)}, status=400)

        if existing_lms_installation():
            return self.send_json({
                "ok": False,
                "error": "Wykryto istniejącą instalację LMS. Tryb wykonawczy jest zablokowany.",
            }, status=409)

        if not CHANGES_ALLOWED:
            return self.send_json({
                "ok": False,
                "error": EXECUTION_BLOCK_REASON or "Zmiany systemowe są zablokowane.",
            }, status=409)

        if not EXECUTION_READY:
            return self.send_json({
                "ok": False,
                "error": "Silnik wykonawczy nie jest jeszcze gotowy do testów.",
            }, status=409)

        try:
            result = execute_plan(
                plan,
                enabled=True,
                destructive_confirmed=destructive_confirmed,
            )
        except ExecutionError as exc:
            return self.send_json({"ok": False, "error": str(exc)}, status=409)

        return self.send_json({"ok": True, "result": result})

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)
def main():
    global CHANGES_ALLOWED, EXECUTION_BLOCK_REASON

    parser = argparse.ArgumentParser(description="LMS Web Setup bootstrap server")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--allow-changes",
        action="store_true",
        help="Enable execution only on a clean dedicated test host.",
    )
    args = parser.parse_args()

    if not WEB_ROOT.is_dir():
        raise SystemExit(f"Missing web directory: {WEB_ROOT}")

    if args.allow_changes:
        if existing_lms_installation():
            CHANGES_ALLOWED = False
            EXECUTION_BLOCK_REASON = "Wykryto istniejącą instalację LMS"
        else:
            CHANGES_ALLOWED = True
            EXECUTION_BLOCK_REASON = ""
    else:
        CHANGES_ALLOWED = False
        EXECUTION_BLOCK_REASON = "Tryb planowania"

    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"LMS Setup listening on http://{args.bind}:{args.port}")
    print(f"Changes allowed: {CHANGES_ALLOWED}")
    if EXECUTION_BLOCK_REASON:
        print(f"Execution blocked: {EXECUTION_BLOCK_REASON}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    main()
