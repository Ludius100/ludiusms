#!/usr/bin/env python3
import grp
import json
import os
import pwd
import secrets
import shutil
import subprocess
from pathlib import Path

from frontend_prepare import prepare_custom_js
from host_ops import HostOperationError, HostOps
from renderer import render_bundle, render_storage_guard
from service_bootstrap import (
    ServiceBootstrapError,
    extract_qbittorrent_temp_password,
    jellyfin_add_library,
    jellyfin_authenticate,
    jellyfin_bootstrap,
    jellyfin_get_libraries,
    jellyfin_install_opensubtitles,
    jellyfin_update_library_preferences,
    jellyfin_token_ok,
    qbittorrent_bootstrap,
    qbittorrent_login_ok,
    wait_http,
)


class ExecutionError(RuntimeError):
    pass


EXECUTION_READY = (
    os.environ.get("LMS_EXECUTION_READY", "0").strip() == "1"
)

INSTALL_ROOT = Path(os.environ.get("LMS_INSTALL_ROOT", "/opt/lms"))
SOURCE_ROOT = Path(
    os.environ.get(
        "LMS_SOURCE_ROOT",
        str(Path(__file__).resolve().parents[1]),
    )
)
SERVICE_USER = "lms"
SERVICE_GROUP = "lms"

API_FILES = ("Dockerfile", "app.py", "config.py", "gunicorn.conf.py")
API_DIRS = ("services", "routes", "modules")
DOCKER_CONFLICTS = (
    "docker.io",
    "docker-compose",
    "docker-compose-v2",
    "docker-doc",
    "docker-buildx",
    "podman-docker",
    "containerd",
    "runc",
)


CommandRunner = HostOps


def _output(argv, timeout=10):
    try:
        proc = subprocess.run(
            list(argv),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _combined_output(argv, timeout=10):
    try:
        proc = subprocess.run(
            list(argv),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return (proc.stdout + "\n" + proc.stderr).strip()


def _command_ok(argv, timeout=10):
    try:
        proc = subprocess.run(
            list(argv),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def _os_release():
    data = {}
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value.strip().strip('"')
    except OSError:
        pass
    return data


def _ubuntu_codename():
    data = _os_release()
    if data.get("ID") != "ubuntu":
        raise ExecutionError("Automatyczna instalacja pakietów wspiera na razie Ubuntu.")
    codename = data.get("UBUNTU_CODENAME") or data.get("VERSION_CODENAME")
    if not codename:
        raise ExecutionError("Nie udało się ustalić kodowej nazwy Ubuntu.")
    return codename


def _installed_packages(names):
    installed = []
    for name in names:
        status = _output(["dpkg-query", "-W", "-f=${Status}", name])
        if "install ok installed" in status:
            installed.append(name)
    return installed


def _service_identity(enabled):
    if enabled:
        try:
            user = pwd.getpwnam(SERVICE_USER)
            group = grp.getgrnam(SERVICE_GROUP)
        except KeyError as exc:
            raise ExecutionError("Brak konta usługowego LMS.") from exc
        return user.pw_uid, group.gr_gid
    return 991, 991


def _safe_library_path(media_root, relative):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ExecutionError("Nieprawidłowa ścieżka biblioteki.")
    return Path(media_root) / rel


def _action_result(action, runner, start, *, status=None, **extra):
    if status is None:
        status = "done" if runner.enabled else "planned"
    return {
        "action_id": action["id"],
        "status": status,
        "operations": len(runner.events) - start,
        **extra,
    }
def _require_root():
    if os.geteuid() != 0:
        raise ExecutionError("Tryb wykonawczy wymaga uruchomienia jako root.")


def ensure_execution_runtime():
    if not EXECUTION_READY:
        raise ExecutionError(
            "Silnik wykonawczy nie jest jeszcze oznaczony jako gotowy do testów."
        )
    _require_root()
    return True


def _ensure_clean_execution_context(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get("actions"), list):
        raise ExecutionError("Nieprawidłowy plan instalacji.")
    ids = [item.get("id") for item in plan["actions"]]
    if len(ids) != len(set(ids)):
        raise ExecutionError("Plan zawiera zduplikowane akcje.")


def execute_plan(plan, *, enabled=False, destructive_confirmed=False):
    _ensure_clean_execution_context(plan)
    if enabled and not EXECUTION_READY:
        raise ExecutionError(
            "Silnik wykonawczy nie jest jeszcze oznaczony jako gotowy do testów."
        )
    if enabled:
        _require_root()

    if plan.get("destructive") and not destructive_confirmed:
        raise ExecutionError(
            "Plan zawiera operację destrukcyjną i wymaga osobnego potwierdzenia."
        )

    runner = CommandRunner(enabled=enabled)
    results = []

    try:
        for action in plan["actions"]:
            result = execute_action(action, plan, runner)
            results.append(result)

            if enabled and result.get("status") == "waiting":
                return {
                    "ok": True,
                    "executed": True,
                    "paused": True,
                    "waiting_for": result,
                    "results": results,
                    "events": runner.events,
                }
    except (HostOperationError, ServiceBootstrapError) as exc:
        raise ExecutionError(str(exc)) from exc

    return {
        "ok": True,
        "executed": bool(enabled),
        "paused": False,
        "results": results,
        "events": runner.events,
    }
def execute_action(action, plan, runner):
    action_id = action.get("id")
    handlers = {
        "docker.install": _docker_install,
        "docker.compose.install": _docker_compose_install,
        "storage.format": _storage_format,
        "storage.mount": _storage_mount,
        "identity.ensure": _identity_ensure,
        "libraries.create": _libraries_create,
        "tailscale.install": _tailscale_install,
        "tailscale.auth": _tailscale_auth,
        "qbittorrent.bootstrap": _qbittorrent_bootstrap,
        "qbittorrent.credentials": _qbittorrent_credentials,
        "jellyfin.bootstrap": _jellyfin_bootstrap,
        "jellyfin.credentials": _jellyfin_credentials,
        "lms.secrets": _lms_secrets,
        "lms.compose": _lms_compose,
        "lms.start": _lms_start,
        "lms.health": _lms_health,
        "jellyfin.libraries": _jellyfin_libraries,
        "jellyfin.opensubtitles": _jellyfin_opensubtitles,
    }
    handler = handlers.get(action_id)
    if handler is None:
        raise ExecutionError(f"Nieobsługiwana akcja: {action_id}")
    return handler(action, plan, runner)


def _planned(action, **extra):
    return {"action_id": action["id"], "status": "planned", **extra}
def _docker_install(action, plan, runner):
    start = len(runner.events)
    codename = _ubuntu_codename()
    arch = _output(["dpkg", "--print-architecture"])
    if arch not in {"amd64", "arm64"}:
        raise ExecutionError(
            "Automatyczna instalacja Docker CE wspiera w testowym buildzie "
            "tylko amd64 i arm64."
        )

    if runner.enabled:
        conflicts = _installed_packages(DOCKER_CONFLICTS)
        if conflicts:
            raise ExecutionError(
                "Wykryto pakiety konfliktujące z Docker CE: "
                + ", ".join(conflicts)
                + ". Installer nie usuwa ich automatycznie."
            )

    runner.run(["apt-get", "update"], action_id=action["id"], timeout=600)
    runner.run(
        ["apt-get", "install", "-y", "ca-certificates", "curl"],
        action_id=action["id"],
        timeout=600,
    )
    runner.ensure_dir("/etc/apt/keyrings", action_id=action["id"], mode=0o755)
    runner.run(
        [
            "curl", "-fsSL",
            "https://download.docker.com/linux/ubuntu/gpg",
            "-o", "/etc/apt/keyrings/docker.asc",
        ],
        action_id=action["id"],
    )
    runner.run(
        ["chmod", "a+r", "/etc/apt/keyrings/docker.asc"],
        action_id=action["id"],
    )

    source = (
        "Types: deb\n"
        "URIs: https://download.docker.com/linux/ubuntu\n"
        f"Suites: {codename}\n"
        "Components: stable\n"
        f"Architectures: {arch}\n"
        "Signed-By: /etc/apt/keyrings/docker.asc\n"
    )
    runner.write_text(
        "/etc/apt/sources.list.d/docker.sources",
        source,
        action_id=action["id"],
        mode=0o644,
    )
    runner.run(["apt-get", "update"], action_id=action["id"], timeout=600)
    runner.run(
        [
            "apt-get", "install", "-y",
            "docker-ce", "docker-ce-cli", "containerd.io",
            "docker-buildx-plugin", "docker-compose-plugin",
        ],
        action_id=action["id"],
        timeout=900,
    )
    runner.run(
        ["systemctl", "enable", "--now", "docker"],
        action_id=action["id"],
    )
    return _action_result(action, runner, start)


def _docker_compose_install(action, plan, runner):
    start = len(runner.events)
    package = "docker-compose-v2"

    if runner.enabled:
        docker_path = shutil.which("docker")
        owner = _output(["dpkg-query", "-S", docker_path]) if docker_path else ""
        if owner and not owner.startswith("docker.io:"):
            package = "docker-compose-plugin"

    runner.run(["apt-get", "update"], action_id=action["id"], timeout=600)
    runner.run(
        ["apt-get", "install", "-y", package],
        action_id=action["id"],
        timeout=600,
    )
    return _action_result(action, runner, start, package=package)


def _storage_format(action, plan, runner):
    start = len(runner.events)
    disk = action.get("details", {}).get("disk")
    if not disk or not disk.startswith("/dev/"):
        raise ExecutionError("Nieprawidłowy dysk w planie.")

    if runner.enabled:
        if _output(["lsblk", "-dn", "-o", "TYPE", disk]) != "disk":
            raise ExecutionError("Wybrane urządzenie nie jest dyskiem blokowym.")
        if _output(["lsblk", "-nr", "-o", "TYPE", disk]).splitlines() != ["disk"]:
            raise ExecutionError(
                "Dysk ma partycje lub podurządzenia. Formatowanie zablokowane."
            )
        if _output(["lsblk", "-dn", "-o", "FSTYPE", disk]):
            raise ExecutionError(
                "Dysk ma już system plików. Formatowanie zablokowane."
            )
        if _output(["lsblk", "-nr", "-o", "MOUNTPOINTS", disk]):
            raise ExecutionError("Dysk lub podurządzenie jest zamontowane.")
        if _output(["findmnt", "-rn", "-S", disk]):
            raise ExecutionError("Wybrany dysk jest obecnie zamontowany.")

    runner.run(
        ["mkfs.ext4", "-F", disk],
        action_id=action["id"],
        timeout=900,
    )
    return _action_result(action, runner, start)


def _storage_mount(action, plan, runner):
    start = len(runner.events)
    config = plan["config"]
    storage = config["storage"]
    disk = config["disk"]
    mountpoint = Path(storage["mountpoint"])
    media_root = Path(storage["media_root"])

    # Jeśli istniejący filesystem jest już zamontowany, nie dotykamy fstab.
    if media_root != mountpoint:
        runner.ensure_dir(
            media_root,
            action_id=action["id"],
            mode=0o2770,
        )
        return _action_result(
            action,
            runner,
            start,
            persistent_mount="existing",
        )

    runner.ensure_dir(
        mountpoint,
        action_id=action["id"],
        mode=0o755,
    )

    uuid = (
        _output(["blkid", "-s", "UUID", "-o", "value", disk])
        if runner.enabled
        else f"<uuid:{disk}>"
    )
    if runner.enabled and not uuid:
        raise ExecutionError("Nie udało się odczytać UUID wybranego dysku.")

    filesystem = storage.get("filesystem") or "ext4"
    fstab_line = (
        f"UUID={uuid} {mountpoint} {filesystem} "
        "defaults,nofail,x-systemd.device-timeout=10 0 2"
    )
    runner.append_line_once(
        "/etc/fstab",
        fstab_line,
        action_id=action["id"],
    )

    if runner.enabled:
        if not _command_ok(["mountpoint", "-q", str(mountpoint)]):
            runner.run(
                ["mount", str(mountpoint)],
                action_id=action["id"],
                timeout=60,
            )
    else:
        runner.run(
            ["mount", str(mountpoint)],
            action_id=action["id"],
            timeout=60,
        )

    return _action_result(
        action,
        runner,
        start,
        persistent_mount="uuid",
    )


def _identity_ensure(action, plan, runner):
    start = len(runner.events)
    group_exists = runner.enabled and _command_ok(
        ["getent", "group", SERVICE_GROUP]
    )
    user_exists = runner.enabled and _command_ok(
        ["id", "-u", SERVICE_USER]
    )

    if not group_exists:
        runner.run(
            ["groupadd", "--system", SERVICE_GROUP],
            action_id=action["id"],
        )
    if not user_exists:
        runner.run(
            [
                "useradd", "--system",
                "--gid", SERVICE_GROUP,
                "--home-dir", "/nonexistent",
                "--shell", "/usr/sbin/nologin",
                SERVICE_USER,
            ],
            action_id=action["id"],
        )
    return _action_result(action, runner, start)


def _libraries_create(action, plan, runner):
    start = len(runner.events)
    media_root = Path(plan["config"]["storage"]["media_root"])
    uid, gid = _service_identity(runner.enabled)

    runner.ensure_dir(
        media_root,
        action_id=action["id"],
        mode=0o2770,
    )
    runner.chown(
        media_root,
        uid,
        gid,
        action_id=action["id"],
    )

    for relative in action.get("details", {}).get("paths", []):
        target = _safe_library_path(media_root, relative)
        runner.ensure_dir(
            target,
            action_id=action["id"],
            mode=0o2770,
        )
        runner.chown(
            target,
            uid,
            gid,
            action_id=action["id"],
        )

    return _action_result(
        action,
        runner,
        start,
        media_root=str(media_root),
    )
def _tailscale_install(action, plan, runner):
    start = len(runner.events)
    codename = _ubuntu_codename()

    if codename not in {"jammy", "noble"}:
        raise ExecutionError(
            "Automatyczna instalacja Tailscale nie została jeszcze "
            f"zatwierdzona dla Ubuntu {codename}."
        )

    runner.ensure_dir(
        "/usr/share/keyrings",
        action_id=action["id"],
        mode=0o755,
    )
    runner.run(
        [
            "curl", "-fsSL",
            (
                "https://pkgs.tailscale.com/stable/ubuntu/"
                f"{codename}.noarmor.gpg"
            ),
            "-o",
            "/usr/share/keyrings/tailscale-archive-keyring.gpg",
        ],
        action_id=action["id"],
    )
    runner.run(
        [
            "curl", "-fsSL",
            (
                "https://pkgs.tailscale.com/stable/ubuntu/"
                f"{codename}.tailscale-keyring.list"
            ),
            "-o",
            "/etc/apt/sources.list.d/tailscale.list",
        ],
        action_id=action["id"],
    )
    runner.run(
        ["apt-get", "update"],
        action_id=action["id"],
        timeout=600,
    )
    runner.run(
        ["apt-get", "install", "-y", "tailscale"],
        action_id=action["id"],
        timeout=600,
    )
    runner.run(
        ["systemctl", "enable", "--now", "tailscaled"],
        action_id=action["id"],
    )
    return _action_result(action, runner, start)


def _tailscale_auth_url():
    command = [
        "tailscale",
        "up",
        "--timeout=5s",
    ]
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
            shell=False,
        )
        output = (proc.stdout + "\n" + proc.stderr).strip()
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        output = (stdout + "\n" + stderr).strip()

    import re
    match = re.search(
        r"https://[^\s]+tailscale[^\s]*",
        output,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"https://login\.tailscale\.com/[^\s]+",
            output,
            re.IGNORECASE,
        )
    return match.group(0).rstrip(".,)") if match else None


def _tailscale_auth(action, plan, runner):
    start = len(runner.events)

    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            interaction="tailscale-auth",
        )

    status = _output(["tailscale", "status", "--json"])
    if (
        '"BackendState": "Running"' in status
        or '"BackendState":"Running"' in status
    ):
        return _action_result(
            action,
            runner,
            start,
            status="done",
        )

    auth_url = _tailscale_auth_url()
    if not auth_url:
        raise ExecutionError(
            "Tailscale nie zwrócił adresu logowania."
        )

    return _action_result(
        action,
        runner,
        start,
        status="waiting",
        interaction="tailscale-auth",
        auth_url=auth_url,
    )


def _read_env_file(path):
    result = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def service_base_url(plan, port, *, enabled=True):
    bind = _runtime_bind(plan, enabled)
    host = "127.0.0.1" if bind == "0.0.0.0" else bind
    return f"http://{host}:{int(port)}"


def _qbittorrent_bootstrap(action, plan, runner):
    start = len(runner.events)

    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            handler="qbittorrent-webui-bootstrap",
        )

    base = service_base_url(plan, 8080, enabled=True)
    wait_http(base, "/", timeout=180)

    credentials = _read_env_file(
        INSTALL_ROOT / "secrets" / "qbittorrent.env"
    )
    username = credentials.get("QBITTORRENT_USERNAME")
    password = credentials.get("QBITTORRENT_PASSWORD")
    if not username or not password:
        raise ExecutionError(
            "Brak wygenerowanych danych logowania qBittorrent."
        )

    if qbittorrent_login_ok(base, username, password):
        return _action_result(
            action,
            runner,
            start,
            status="done",
            already_configured=True,
        )

    logs = _combined_output(
        ["docker", "logs", "--tail", "300", "lms-qbittorrent"],
        timeout=20,
    )
    temporary_password = extract_qbittorrent_temp_password(logs)
    last_error = None
    for attempt in range(1, 6):
        try:
            qbittorrent_bootstrap(
                base,
                temporary_password=temporary_password,
                username=username,
                password=password,
                save_path="/nas/Downloads",
            )
            return _action_result(action, runner, start, status="done")
        except ServiceBootstrapError as exc:
            last_error = exc
            if attempt < 5:
                import time
                time.sleep(2)

    raise ExecutionError(
        f"Nie udało się skonfigurować qBittorrent po 5 próbach: {last_error}"
    )


def _qbittorrent_credentials(action, plan, runner):
    start = len(runner.events)
    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            interaction="qbittorrent-credentials",
        )

    secret_file = INSTALL_ROOT / "secrets" / "qbittorrent.env"
    if secret_file.exists():
        credentials = _read_env_file(secret_file)
        username = credentials.get("QBITTORRENT_USERNAME")
        password = credentials.get("QBITTORRENT_PASSWORD")
        if username and password:
            base = service_base_url(plan, 8080, enabled=True)
            if qbittorrent_login_ok(base, username, password):
                return _action_result(
                    action,
                    runner,
                    start,
                    status="done",
                )

    return _action_result(
        action,
        runner,
        start,
        status="waiting",
        interaction="qbittorrent-credentials",
    )


def _jellyfin_bootstrap(action, plan, runner):
    start = len(runner.events)

    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            handler="jellyfin-startup-api",
        )

    base = service_base_url(plan, 8096, enabled=True)
    wait_http(base, "/System/Info/Public", timeout=180)

    credentials = _read_env_file(
        INSTALL_ROOT / "secrets" / "jellyfin_admin.env"
    )
    username = credentials.get("JELLYFIN_ADMIN_USERNAME")
    password = credentials.get("JELLYFIN_ADMIN_PASSWORD")
    if not username or not password:
        raise ExecutionError(
            "Brak wygenerowanych danych administratora Jellyfin."
        )

    try:
        token = jellyfin_authenticate(
            base,
            username=username,
            password=password,
        )
        already_configured = True
    except ServiceBootstrapError:
        token = jellyfin_bootstrap(
            base,
            username=username,
            password=password,
        )
        already_configured = False

    key_file = INSTALL_ROOT / "secrets" / "jellyfin_api_key"
    runner.write_text(
        key_file,
        token + "\n",
        action_id=action["id"],
        mode=0o600,
        preserve_inode=True,
    )
    uid, gid = _service_identity(runner.enabled)
    runner.chown(
        key_file,
        uid,
        gid,
        action_id=action["id"],
    )
    runner.chmod(
        key_file,
        0o400,
        action_id=action["id"],
    )
    return _action_result(
        action,
        runner,
        start,
        status="done",
        already_configured=already_configured,
    )


def _jellyfin_credentials(action, plan, runner):
    start = len(runner.events)
    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            interaction="jellyfin-credentials",
        )

    key_file = INSTALL_ROOT / "secrets" / "jellyfin_api_key"
    if key_file.exists():
        token = key_file.read_text(encoding="utf-8").strip()
        if token:
            base = service_base_url(plan, 8096, enabled=True)
            if jellyfin_token_ok(base, token):
                uid, gid = _service_identity(runner.enabled)
                runner.chown(
                    key_file,
                    uid,
                    gid,
                    action_id=action["id"],
                )
                runner.chmod(
                    key_file,
                    0o400,
                    action_id=action["id"],
                )
                return _action_result(
                    action,
                    runner,
                    start,
                    status="done",
                )

    return _action_result(
        action,
        runner,
        start,
        status="waiting",
        interaction="jellyfin-credentials",
    )


def _lms_secrets(action, plan, runner):
    start = len(runner.events)
    secret_dir = INSTALL_ROOT / "secrets"

    runner.ensure_dir(
        secret_dir,
        action_id=action["id"],
        mode=0o700,
    )

    qb_file = secret_dir / "qbittorrent.env"
    jellyfin_admin_file = secret_dir / "jellyfin_admin.env"
    jellyfin_key_file = secret_dir / "jellyfin_api_key"

    qb_password = (
        plan.get("config", {}).get("qbittorrent_password")
        or (secrets.token_urlsafe(30) if runner.enabled else "<generated>")
    )
    jellyfin_password = (
        secrets.token_urlsafe(30)
        if runner.enabled
        else "<generated>"
    )

    if not (runner.enabled and qb_file.exists()):
        runner.write_text(
            qb_file,
            (
                "QBITTORRENT_USERNAME=lmsadmin\n"
                f"QBITTORRENT_PASSWORD={qb_password}\n"
            ),
            action_id=action["id"],
            mode=0o600,
        )

    if not (runner.enabled and jellyfin_admin_file.exists()):
        runner.write_text(
            jellyfin_admin_file,
            (
                "JELLYFIN_ADMIN_USERNAME=lmsadmin\n"
                f"JELLYFIN_ADMIN_PASSWORD={jellyfin_password}\n"
            ),
            action_id=action["id"],
            mode=0o600,
        )

    if not (runner.enabled and jellyfin_key_file.exists()):
        runner.write_text(
            jellyfin_key_file,
            "",
            action_id=action["id"],
            mode=0o600,
        )

    uid, gid = _service_identity(runner.enabled)
    runner.chown(
        jellyfin_key_file,
        uid,
        gid,
        action_id=action["id"],
    )
    runner.chmod(
        jellyfin_key_file,
        0o400,
        action_id=action["id"],
    )

    return _action_result(action, runner, start)


def _runtime_bind(plan, enabled):
    if plan["config"]["network"] == "tailscale":
        if enabled:
            ip = _output(["tailscale", "ip", "-4"])
            if not ip:
                raise ExecutionError(
                    "Tailscale nie ma jeszcze adresu IPv4."
                )
            return ip.splitlines()[0].strip()
        return "<tailscale-ip>"

    return "127.0.0.1"


def _homepage_allowed_hosts(bind_address, enabled):
    hosts = {
        "localhost:3000",
        "127.0.0.1:3000",
        "lms-homepage:3000",
    }

    if bind_address not in {"0.0.0.0", "127.0.0.1"}:
        if not bind_address.startswith("<"):
            hosts.add(f"{bind_address}:3000")

    if enabled:
        hostname = _output(["hostname"])
        if hostname:
            hosts.add(f"{hostname}:3000")

        for address in _output(["hostname", "-I"]).split():
            if address:
                hosts.add(f"{address}:3000")

    return ",".join(sorted(hosts))


def _lms_compose(action, plan, runner):
    start = len(runner.events)
    uid, gid = _service_identity(runner.enabled)
    bind_address = _runtime_bind(plan, runner.enabled)
    allowed_hosts = _homepage_allowed_hosts(
        bind_address,
        runner.enabled,
    )

    if runner.enabled:
        api_source = SOURCE_ROOT / "dashboard-api"
        homepage_source = SOURCE_ROOT / "homepage"

        if not api_source.is_dir() or not homepage_source.is_dir():
            raise ExecutionError(
                f"Niekompletny pakiet instalacyjny LMS: {SOURCE_ROOT}"
            )

    runner.ensure_dir(
        INSTALL_ROOT,
        action_id=action["id"],
        mode=0o755,
    )
    runner.ensure_dir(
        INSTALL_ROOT / "homepage" / "config",
        action_id=action["id"],
        mode=0o755,
    )
    runner.ensure_dir(
        INSTALL_ROOT / "data",
        action_id=action["id"],
        mode=0o750,
    )

    runtime_dirs = [
        INSTALL_ROOT / "homepage" / "config",
        INSTALL_ROOT / "data",
    ]
    services = plan["config"]["services"]
    if services["jellyfin"] == "install":
        runtime_dirs.extend([
            INSTALL_ROOT / "jellyfin" / "config",
            INSTALL_ROOT / "jellyfin" / "cache",
        ])
    if services["qbittorrent"] == "install":
        runtime_dirs.append(
            INSTALL_ROOT / "qbittorrent" / "config"
        )

    for runtime_dir in runtime_dirs:
        runner.ensure_dir(
            runtime_dir,
            action_id=action["id"],
            mode=0o750,
        )
        runner.chown(
            runtime_dir,
            uid,
            gid,
            action_id=action["id"],
            recursive=True,
        )

    if runner.enabled:
        runner.copy_tree_whitelist(
            SOURCE_ROOT / "dashboard-api",
            INSTALL_ROOT / "dashboard-api",
            action_id=action["id"],
            files=API_FILES,
            directories=API_DIRS,
        )
    else:
        runner.events.append({
            "action_id": action["id"],
            "kind": "copy-api-whitelist",
            "status": "planned",
            "source": str(SOURCE_ROOT / "dashboard-api"),
            "destination": str(INSTALL_ROOT / "dashboard-api"),
        })

    bundle = render_bundle(
        plan,
        uid=uid,
        gid=gid,
        bind_address=bind_address,
        allowed_hosts=allowed_hosts,
    )

    for relative, content in bundle.items():
        runner.write_text(
            INSTALL_ROOT / relative,
            content,
            action_id=action["id"],
            mode=0o600 if relative == ".env" else 0o644,
        )

    if runner.enabled:
        source_js = (
            SOURCE_ROOT / "homepage" / "custom.js"
        ).read_text(encoding="utf-8")
        prepared_js = prepare_custom_js(source_js)

        runner.write_text(
            INSTALL_ROOT / "homepage" / "config" / "custom.js",
            prepared_js,
            action_id=action["id"],
            mode=0o644,
        )
        runner.copy_file(
            SOURCE_ROOT / "homepage" / "custom.css",
            INSTALL_ROOT / "homepage" / "config" / "custom.css",
            action_id=action["id"],
            mode=0o644,
        )
        runner.ensure_dir(
            INSTALL_ROOT / "homepage" / "assets",
            action_id=action["id"],
            mode=0o755,
        )
        for name in ("lms-logo.webp", "lms-hero.webp"):
            runner.copy_file(
                SOURCE_ROOT / "homepage" / "assets" / name,
                INSTALL_ROOT / "homepage" / "assets" / name,
                action_id=action["id"],
                mode=0o644,
            )
        # Profil powstaje dopiero podczas instalacji. Imię nie trafia
        # do źródeł, publicznej paczki ani repozytorium.
        runner.write_text(
            INSTALL_ROOT / "homepage" / "assets" / "lms-profile.json",
            json.dumps({"displayName": plan["config"].get("display_name", "")}, ensure_ascii=False) + "\n",
            action_id=action["id"],
            mode=0o644,
        )
    else:
        runner.events.append({
            "action_id": action["id"],
            "kind": "prepare-portable-frontend",
            "status": "planned",
        })

    return _action_result(
        action,
        runner,
        start,
        install_root=str(INSTALL_ROOT),
        bind_address=bind_address,
    )


def _verify_storage_mount(plan):
    """Nie uruchamiaj Docker na pustym katalogu pod odmontowanym NAS."""
    storage = plan["config"]["storage"]
    mountpoint = str(storage["mountpoint"])
    disk = str(plan["config"]["disk"])
    mounted = _output(["findmnt", "--mountpoint", mountpoint, "-n", "-o", "SOURCE"])
    if not mounted:
        raise ExecutionError(
            f"Magazyn LMS nie jest zamontowany w {mountpoint}; blokuję uruchomienie kontenerów."
        )
    # /dev/sdb i /dev/disk/by-uuid/... mogą wskazywać to samo urządzenie.
    try:
        if not os.path.samefile(mounted, disk):
            raise ExecutionError(
                f"Pod {mountpoint} znajduje się inny dysk niż wybrany magazyn LMS."
            )
    except OSError as exc:
        raise ExecutionError("Nie udało się zweryfikować urządzenia magazynu LMS.") from exc
    media_root = str(storage["media_root"])
    if not Path(media_root).is_dir():
        raise ExecutionError("Brak katalogu danych LMS na zamontowanym dysku.")


def _lms_start(action, plan, runner):
    start = len(runner.events)
    if runner.enabled:
        _verify_storage_mount(plan)
    # Na VM mogły przetrwać stare kontenery ze starym widokiem /nas.
    # Odtworzenie podłącza je do aktualnego magazynu bez usuwania wolumenów.
    runner.run(
        [
            "docker", "compose",
            "--project-directory", str(INSTALL_ROOT),
            "--env-file", str(INSTALL_ROOT / ".env"),
            "-f", str(INSTALL_ROOT / "compose.yaml"),
            "up", "-d", "--build", "--force-recreate",
        ],
        action_id=action["id"],
        timeout=1800,
    )
    if runner.enabled and str(plan["config"]["storage"]["mountpoint"]) != "/":
        unit = render_storage_guard(plan)
        runner.write_text(
            "/etc/systemd/system/lms-storage-guard.service",
            unit,
            action_id=action["id"],
            mode=0o644,
        )
        runner.run(["systemctl", "daemon-reload"], action_id=action["id"])
        runner.run(
            ["systemctl", "enable", "lms-storage-guard.service"],
            action_id=action["id"],
        )
    return _action_result(action, runner, start)


def _lms_health(action, plan, runner):
    start = len(runner.events)

    required = [
        "lms-gateway",
        "lms-homepage",
        "lms-api",
    ]
    services = plan.get("config", {}).get("services", {})
    if services.get("jellyfin") == "install":
        required.append("lms-jellyfin")
    if services.get("qbittorrent") == "install":
        required.append("lms-qbittorrent")

    for container in required:
        if runner.enabled:
            running = _output([
                "docker",
                "inspect",
                "-f",
                "{{.State.Running}}",
                container,
            ])
            if running != "true":
                raise ExecutionError(
                    f"Kontener {container} nie działa po instalacji."
                )
        else:
            runner.events.append({
                "action_id": action["id"],
                "kind": "container-health",
                "status": "planned",
                "container": container,
            })

    # Docker inspect może wskazywać poprawny bind mount, choć proces widzi
    # pusty katalog sprzed montowania. Sprawdzamy realne biblioteki w środku.
    paths = next((a.get("details", {}).get("paths", [])
                  for a in plan.get("actions", [])
                  if a.get("id") == "libraries.create"), [])
    uid, gid = _service_identity(runner.enabled)
    checks = [("lms-api", "/nas")]
    if services.get("qbittorrent") == "install":
        checks.append(("lms-qbittorrent", "/nas"))
    if services.get("jellyfin") == "install":
        checks.append(("lms-jellyfin", "/media"))
    for container, root in checks:
        for relative in paths:
            location = f"{root}/{relative}"
            if runner.enabled:
                for permission in (("-d", "-w") if container != "lms-jellyfin" else ("-d",)):
                    if not _command_ok([
                        "docker", "exec", "--user", f"{uid}:{gid}",
                        container, "test", permission, location,
                    ]):
                        problem = "nie widzi" if permission == "-d" else "nie może zapisywać w"
                        raise ExecutionError(
                            f"{container} {problem} biblioteki {location}. "
                            "Sprawdź montowanie NAS i uprawnienia katalogów."
                        )
            else:
                runner.events.append({
                    "action_id": action["id"], "kind": "library-visibility",
                    "status": "planned", "container": container,
                    "path": location,
                })
    return _action_result(
        action,
        runner,
        start,
        containers=required,
    )


def _jellyfin_libraries(action, plan, runner):
    start = len(runner.events)

    if not runner.enabled:
        return _action_result(
            action,
            runner,
            start,
            status="planned",
            handler="jellyfin-api",
        )

    key_file = INSTALL_ROOT / "secrets" / "jellyfin_api_key"
    token = key_file.read_text(encoding="utf-8").strip()
    if not token:
        raise ExecutionError(
            "Brak tokenu Jellyfin potrzebnego do utworzenia bibliotek."
        )

    base = service_base_url(plan, 8096, enabled=True)
    existing = jellyfin_get_libraries(base, token)

    names = {
        "Filmy": "Filmy",
        "Seriale": "Seriale",
        "Anime/Filmy": "Anime • Filmy",
        "Anime/Seriale": "Anime • Seriale",
    }

    existing_names = {
        item.get("Name")
        for item in existing
        if isinstance(item, dict)
    }
    existing_locations = {
        location
        for item in existing
        if isinstance(item, dict)
        for location in (item.get("Locations") or [])
    }

    created = []
    skipped = []

    for library in action.get("details", {}).get("libraries", []):
        relative = library["path"]
        location = "/media/" + relative.strip("/")
        name = names.get(
            relative,
            relative.replace("/", " • "),
        )

        if name in existing_names or location in existing_locations:
            skipped.append(name)
            continue

        jellyfin_add_library(
            base,
            token,
            name=name,
            collection_type=library["content_type"],
            paths=[location],
        )

    # Apply language preferences to both newly created and existing LMS libraries.
    refreshed = jellyfin_get_libraries(base, token)
    wanted_locations = {
        "/media/" + item["path"].strip("/")
        for item in action.get("details", {}).get("libraries", [])
    }
    for item in refreshed:
        if not isinstance(item, dict):
            continue
        if not wanted_locations.intersection(item.get("Locations") or []):
            continue
        item_id = item.get("ItemId")
        if not item_id:
            continue
        jellyfin_update_library_preferences(
            base,
            token,
            item_id=item_id,
            options=item.get("LibraryOptions") or {},
            metadata_language=action.get("details", {}).get("metadata_language", "pl"),
            subtitle_language=action.get("details", {}).get("subtitle_language", "pl"),
        )
        created.append(name)

    return _action_result(
        action,
        runner,
        start,
        status="done",
        created=created,
        skipped=skipped,
    )


def _jellyfin_opensubtitles(action, plan, runner):
    start = len(runner.events)
    if not runner.enabled:
        return _action_result(
            action, runner, start, status="planned", handler="jellyfin-package-api"
        )
    key_file = INSTALL_ROOT / "secrets" / "jellyfin_api_key"
    token = key_file.read_text(encoding="utf-8").strip()
    if not token:
        raise ExecutionError("Brak tokenu Jellyfin do instalacji Open Subtitles.")
    base = service_base_url(plan, 8096, enabled=True)
    jellyfin_install_opensubtitles(base, token)
    runner.run(
        ["docker", "restart", "lms-jellyfin"],
        action_id=action["id"],
        timeout=120,
    )
    wait_http(base, "/System/Info/Public", timeout=180)
    return _action_result(
        action,
        runner,
        start,
        status="done",
        restarted="lms-jellyfin",
    )
