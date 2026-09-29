[Reading 105 lines from start (total: 105 lines, 0 remaining)]

#!/usr/bin/env python3
import os
from pathlib import Path

from service_bootstrap import (
    ServiceBootstrapError,
    jellyfin_authenticate,
    qbittorrent_login_ok,
)


class InteractionInputError(ValueError):
    pass


def _clean_credential(
    value,
    name,
    *,
    min_length=1,
    max_length=512,
    strip=True,
):
    if not isinstance(value, str):
        raise InteractionInputError(f"{name}: nieprawidłowa wartość.")
    if strip:
        value = value.strip()
    if len(value) < min_length:
        raise InteractionInputError(f"{name}: wartość jest wymagana.")
    if len(value) > max_length:
        raise InteractionInputError(f"{name}: wartość jest zbyt długa.")
    if "\n" in value or "\r" in value:
        raise InteractionInputError(f"{name}: niedozwolony znak nowej linii.")
    return value


def _write_secret(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)

    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.chmod(0o600)
    os.replace(tmp, path)
    path.chmod(0o600)


def save_existing_qbittorrent_credentials(
    *,
    base_url,
    username,
    password,
    secret_path,
):
    username = _clean_credential(username, "Login qBittorrent")
    password = _clean_credential(
        password,
        "Hasło qBittorrent",
        strip=False,
    )

    if not qbittorrent_login_ok(base_url, username, password):
        raise InteractionInputError(
            "qBittorrent odrzucił podany login lub hasło."
        )

    _write_secret(
        secret_path,
        (
            f"QBITTORRENT_USERNAME={username}\n"
            f"QBITTORRENT_PASSWORD={password}\n"
        ),
    )
    return True


def save_existing_jellyfin_credentials(
    *,
    base_url,
    username,
    password,
    token_path,
):
    username = _clean_credential(username, "Login Jellyfin")
    password = _clean_credential(
        password,
        "Hasło Jellyfin",
        strip=False,
    )

    try:
        token = jellyfin_authenticate(
            base_url,
            username=username,
            password=password,
        )
    except ServiceBootstrapError as exc:
        raise InteractionInputError(
            "Jellyfin odrzucił podany login lub hasło."
        ) from exc

    token = _clean_credential(token, "Token Jellyfin")
    _write_secret(token_path, token + "\n")
    return True

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]