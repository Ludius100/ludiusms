[Reading 1000 lines from start (total: 1219 lines, 219 remaining)]

#!/usr/bin/env python3
import grp
import os
import pwd
import secrets
import shutil
import subprocess
from pathlib import Path

from frontend_prepare import prepare_custom_js
from host_ops import HostOperationError, HostOps
from renderer import render_bundle
from service_bootstrap import (
    ServiceBootstrapError,
    extract_qbittorrent_temp_password,
    jellyfin_add_library,
    jellyfin_authenticate,
    jellyfin_bootstrap,
    jellyfin_get_libraries,
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
    qbittorrent_bootstrap(
        base,
        temporary_password=temporary_password,
        username=username,
        password=password,
        save_path="/nas/Downloads",
    )
    return _action_result(action, runner, start, status="done")


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
        secrets.token_urlsafe(30)
        if runner.enabled
        else "<generated>"
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

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]