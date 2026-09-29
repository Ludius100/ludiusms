[Reading 60 lines from start (total: 60 lines, 0 remaining)]

#!/usr/bin/env python3
from pathlib import Path


class FinalCredentialsError(RuntimeError):
    pass


def _read_env(path):
    path = Path(path)
    if not path.is_file():
        raise FinalCredentialsError(
            f"Brak wymaganego pliku danych logowania: {path.name}"
        )

    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value
    return result


def collect_managed_credentials(plan, install_root):
    install_root = Path(install_root)
    services = plan.get("config", {}).get("services", {})
    result = {}

    if services.get("jellyfin") == "install":
        env = _read_env(
            install_root / "secrets" / "jellyfin_admin.env"
        )
        username = env.get("JELLYFIN_ADMIN_USERNAME")
        password = env.get("JELLYFIN_ADMIN_PASSWORD")
        if not username or not password:
            raise FinalCredentialsError(
                "Niekompletne dane administratora Jellyfin."
            )
        result["jellyfin"] = {
            "username": username,
            "password": password,
        }

    if services.get("qbittorrent") == "install":
        env = _read_env(
            install_root / "secrets" / "qbittorrent.env"
        )
        username = env.get("QBITTORRENT_USERNAME")
        password = env.get("QBITTORRENT_PASSWORD")
        if not username or not password:
            raise FinalCredentialsError(
                "Niekompletne dane qBittorrent."
            )
        result["qbittorrent"] = {
            "username": username,
            "password": password,
        }

    return result

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]