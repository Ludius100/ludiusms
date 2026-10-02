#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path

LIBRARY_DEFS = {
    "movies": {"name": "Filmy", "paths": ["Filmy"], "jellyfin": ["movies"]},
    "series": {"name": "Seriale", "paths": ["Seriale"], "jellyfin": ["tvshows"]},
    "anime": {
        "name": "Anime",
        "paths": ["Anime/Filmy", "Anime/Seriale"],
        "jellyfin": ["movies", "tvshows"],
    },
}
SERVICE_IDS = ("tailscale", "jellyfin", "qbittorrent")
SERVICE_PLANS = ("existing", "install", "skip")
NETWORK_MODES = ("tailscale", "direct")
JELLYFIN_LANGUAGES = ("pl", "en", "de", "fr", "es", "it", "ja")


class PlanError(ValueError):
    pass


def _disk_candidates(host):
    return [
        disk for disk in host.get("disks", [])
        if disk.get("type") == "disk"
    ]


def _find_disk(host, path):
    for disk in _disk_candidates(host):
        if disk.get("path") == path:
            return disk
    raise PlanError("Wybrany dysk nie jest już dostępny.")
def _normalize_libraries(value):
    if not isinstance(value, list) or not value:
        raise PlanError("Wybierz co najmniej jedną bibliotekę.")
    result = []
    for item in value:
        if item not in LIBRARY_DEFS:
            raise PlanError("Nieznany typ biblioteki.")
        if item not in result:
            result.append(item)
    return result


def _normalize_services(value, host):
    if not isinstance(value, dict):
        raise PlanError("Nieprawidłowa konfiguracja usług.")

    detected = host.get("components", {})
    result = {}
    for service_id in SERVICE_IDS:
        installed = bool(detected.get(service_id, {}).get("installed"))
        choice = value.get(service_id)
        if choice not in SERVICE_PLANS:
            choice = "existing" if installed else "install"

        if installed and choice == "install":
            raise PlanError(
                f"{service_id}: istniejąca instalacja nie będzie automatycznie przeinstalowywana."
            )
        if not installed and choice == "existing":
            raise PlanError(f"{service_id}: nie wykryto istniejącej instalacji.")
        result[service_id] = choice
    return result
def _storage_strategy(disk):
    if disk.get("read_only"):
        raise PlanError("Wybrany dysk jest tylko do odczytu.")
    if disk.get("is_system"):
        raise PlanError("Dysk systemowy jest chroniony i nie może być magazynem LMS.")

    children = disk.get("children") or []
    filesystem = disk.get("filesystem")
    mountpoints = disk.get("mountpoints") or []

    if children:
        raise PlanError(
            "Wybrany dysk ma istniejące partycje. "
            "Testowy installer nie będzie automatycznie modyfikował takiego układu."
        )

    if filesystem:
        mountpoint = mountpoints[0] if mountpoints else "/srv/lms-media"
        media_root = (
            str(Path(mountpoint) / "LMS")
            if mountpoints
            else "/srv/lms-media"
        )
        return {
            "mode": "existing-filesystem",
            "filesystem": filesystem,
            "mountpoint": mountpoint,
            "media_root": media_root,
            "destructive": False,
        }

    return {
        "mode": "format-ext4",
        "filesystem": "ext4",
        "mountpoint": "/srv/lms-media",
        "media_root": "/srv/lms-media",
        "destructive": True,
    }
def _normalize_qbittorrent_password(value):
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not 10 <= len(value) <= 128:
        raise PlanError("Hasło qBittorrent musi mieć 10–128 znaków.")
    if not value.isascii() or any(
        ch.isspace() or ch in "\\\"'\\\\$" for ch in value
    ):
        raise PlanError(
            "Hasło qBittorrent: użyj znaków ASCII bez spacji, cudzysłowów, "
            "ukośnika odwrotnego i znaku dolara."
        )
    return value


def _normalize_jellyfin_settings(value, enabled):
    if not enabled:
        return {
            "metadata_language": "pl",
            "subtitle_language": "pl",
            "opensubtitles": False,
        }
    value = value if isinstance(value, dict) else {}
    metadata = value.get("metadata_language", "pl")
    subtitles = value.get("subtitle_language", "pl")
    if metadata not in JELLYFIN_LANGUAGES or subtitles not in JELLYFIN_LANGUAGES:
        raise PlanError("Nieobsługiwany język konfiguracji Jellyfin.")
    return {
        "metadata_language": metadata,
        "subtitle_language": subtitles,
        "opensubtitles": bool(value.get("opensubtitles", False)),
    }


def normalize_config(payload, host):
    if not isinstance(payload, dict):
        raise PlanError("Nieprawidłowy format konfiguracji.")

    disk = _find_disk(host, payload.get("disk"))
    storage = _storage_strategy(disk)
    libraries = _normalize_libraries(payload.get("libraries"))
    services = _normalize_services(payload.get("services", {}), host)

    network = payload.get("network", "tailscale")
    if network not in NETWORK_MODES:
        raise PlanError("Nieznany tryb sieci.")
    if network == "tailscale" and services["tailscale"] == "skip":
        raise PlanError("Dostęp przez Tailscale wymaga włączonej usługi Tailscale.")

    jellyfin = _normalize_jellyfin_settings(payload.get("jellyfin"), services["jellyfin"] != "skip")

    result = {
        "disk": disk.get("path"),
        "storage": storage,
        "libraries": libraries,
        "services": services,
        "network": network,
        "jellyfin": jellyfin,
    }
    if services["qbittorrent"] == "install":
        password = _normalize_qbittorrent_password(
            payload.get("qbittorrent_password")
        )
        if password:
            result["qbittorrent_password"] = password
    return result


def _action(action_id, phase, title, *, destructive=False, interaction=False, details=None):
    return {
        "id": action_id,
        "phase": phase,
        "title": title,
        "destructive": destructive,
        "interaction": interaction,
        "details": details or {},
    }
def build_plan(payload, host):
    config = normalize_config(payload, host)
    actions = []

    if not host.get("docker", {}).get("installed"):
        actions.append(_action(
            "docker.install", "dependencies", "Zainstaluj Docker Engine i Compose",
        ))
    elif not host.get("docker", {}).get("compose_installed"):
        actions.append(_action(
            "docker.compose.install", "dependencies", "Zainstaluj Docker Compose plugin",
        ))

    storage = config["storage"]
    if storage["mode"] == "format-ext4":
        actions.append(_action(
            "storage.format", "storage", "Sformatuj wybrany dysk jako ext4",
            destructive=True,
            details={"disk": config["disk"], "filesystem": "ext4"},
        ))
    actions.append(_action(
        "storage.mount", "storage", "Przygotuj punkt montowania magazynu",
        details={"disk": config["disk"], "mountpoint": storage["mountpoint"]},
    ))
    actions.append(_action(
        "identity.ensure", "storage", "Utwórz konto i grupę usług LMS",
    ))
    library_paths = ["Downloads"]
    for library_id in config["libraries"]:
        library_paths.extend(LIBRARY_DEFS[library_id]["paths"])
    actions.append(_action(
        "libraries.create", "storage", "Utwórz strukturę bibliotek",
        details={"paths": library_paths},
    ))

    services = config["services"]
    if services["tailscale"] == "install":
        actions.append(_action(
            "tailscale.install", "services", "Zainstaluj Tailscale",
        ))
    if config["network"] == "tailscale":
        actions.append(_action(
            "tailscale.auth", "services", "Połącz serwer z Tailscale",
            interaction=True,
        ))

    actions.append(
        _action("lms.secrets", "lms", "Wygeneruj lokalne sekrety LMS")
    )

    if services["qbittorrent"] == "existing":
        actions.append(_action(
            "qbittorrent.credentials",
            "configure",
            "Połącz LMS z istniejącym qBittorrent",
            interaction=True,
        ))
    if services["jellyfin"] == "existing":
        actions.append(_action(
            "jellyfin.credentials",
            "configure",
            "Połącz LMS z istniejącym Jellyfin",
            interaction=True,
        ))

    actions.extend([
        _action("lms.compose", "lms", "Wygeneruj konfigurację kontenerów LMS"),
        _action("lms.start", "lms", "Uruchom usługi LMS"),
    ])

    if services["qbittorrent"] == "install":
        actions.append(_action(
            "qbittorrent.bootstrap",
            "configure",
            "Ustaw bezpieczne dane logowania qBittorrent",
        ))

    if services["jellyfin"] == "install":
        actions.append(_action(
            "jellyfin.bootstrap",
            "configure",
            "Przeprowadź automatyczną konfigurację Jellyfin",
            interaction=True,
        ))

    if services["jellyfin"] != "skip":
        jellyfin_libraries = []
        for library_id in config["libraries"]:
            definition = LIBRARY_DEFS[library_id]
            for index, path in enumerate(definition["paths"]):
                jellyfin_libraries.append({
                    "path": path,
                    "content_type": definition["jellyfin"][index],
                })
        actions.append(_action(
            "jellyfin.libraries",
            "configure",
            "Skonfiguruj biblioteki Jellyfin",
            details={
                "libraries": jellyfin_libraries,
                "metadata_language": config["jellyfin"]["metadata_language"],
                "subtitle_language": config["jellyfin"]["subtitle_language"],
            },
        ))
        if config["jellyfin"]["opensubtitles"]:
            actions.append(_action(
                "jellyfin.opensubtitles",
                "configure",
                "Zainstaluj wtyczkę Open Subtitles",
            ))

    actions.append(_action(
        "lms.health",
        "verify",
        "Sprawdź stan wszystkich usług",
    ))

    plan = {
        "schema": 1,
        "config": deepcopy(config),
        "actions": actions,
        "destructive": any(item["destructive"] for item in actions),
        "requires_interaction": any(item["interaction"] for item in actions),
    }
    return plan

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]