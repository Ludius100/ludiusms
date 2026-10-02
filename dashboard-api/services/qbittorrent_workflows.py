import time
import re
import urllib.error
import urllib.parse

from config import QBITTORRENT_LIBRARIES
from services.nas import ensure_nas_directory
from services.qbittorrent import (
    format_qb_file,
    format_torrent,
    qb_client,
    qb_find_torrent_by_magnet,
    qb_get,
    qb_post,
    qb_torrent_files,
)


class QBitTorrentError(Exception):
    def __init__(self, message, status_code=400, **details):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            "ok": False,
            "error": message,
            **details,
        }


_SUCCESS_STATUSES = (200, 204)
_INACTIVE_STATES = {
    "pausedDL",
    "pausedUP",
    "stoppedDL",
    "stoppedUP",
    "error",
    "missingFiles",
}
_DOWNLOADING_STATES = {
    "downloading",
    "metaDL",
    "forcedDL",
    "stalledDL",
    "checkingDL",
    "allocating",
}


def _require_success(status, action):
    if status not in _SUCCESS_STATUSES:
        raise RuntimeError(
            f"{action} HTTP {status}"
        )


def _qb_step(opener, endpoint, payload, label):
    """Zwróć czytelny etap awarii bez ujawniania sekretów ani URL magnetu."""
    try:
        status = qb_post(opener, endpoint, payload)
    except urllib.error.HTTPError as exc:
        raise QBitTorrentError(
            f"qBittorrent odrzucił operację {label} (HTTP {exc.code})",
            502,
            operation=label,
            upstreamStatus=exc.code,
        ) from exc
    _require_success(status, label)
    return status


def _safe_torrent_folder_name(name, fallback):
    value = str(name or "").strip()

    for char in '<>:"/\\|?*':
        value = value.replace(char, "_")

    value = value.strip(" .")
    return value or fallback


def get_qbittorrent_libraries():
    return [
        {
            "id": library_id,
            "name": library["name"],
        }
        for library_id, library
        in QBITTORRENT_LIBRARIES.items()
    ]


def get_qbittorrent_status():
    opener = qb_client()
    transfer = qb_get(
        opener,
        "/api/v2/transfer/info",
    ) or {}

    torrents = qb_get(
        opener,
        "/api/v2/torrents/info",
    ) or []

    formatted = [
        format_torrent(torrent)
        for torrent in torrents
    ]

    active = [
        torrent
        for torrent in formatted
        if torrent["state"] not in _INACTIVE_STATES
    ]

    downloading = [
        torrent
        for torrent in formatted
        if torrent["state"] in _DOWNLOADING_STATES
    ]

    return {
        "online": True,
        "downloadSpeed": transfer.get(
            "dl_info_speed",
            0,
        ),
        "uploadSpeed": transfer.get(
            "up_info_speed",
            0,
        ),
        "downloaded": transfer.get(
            "dl_info_data",
            0,
        ),
        "uploaded": transfer.get(
            "up_info_data",
            0,
        ),
        "total": len(formatted),
        "active": len(active),
        "downloading": len(downloading),
        "torrents": formatted,
    }


def prepare_magnet(magnet, library_id="downloads"):
    magnet = str(magnet or "").strip()

    if not magnet:
        raise QBitTorrentError(
            "Brak linku magnet",
            400,
        )

    if not magnet.lower().startswith("magnet:?"):
        raise QBitTorrentError(
            "Dozwolone są tylko linki magnet",
            400,
        )

    if len(magnet) > 16_384:
        raise QBitTorrentError(
            "Link magnet jest zbyt długi",
            400,
        )

    library_id = str(
        library_id or "downloads"
    ).strip()
    library = QBITTORRENT_LIBRARIES.get(
        library_id
    )

    if not library:
        raise QBitTorrentError(
            "Nieprawidłowa biblioteka",
            400,
        )

    opener = qb_client()
    before = qb_get(
        opener,
        "/api/v2/torrents/info",
    ) or []

    before_hashes = {
        torrent.get("hash")
        for torrent in before
        if torrent.get("hash")
    }

    expected_hash = (
        qb_find_torrent_by_magnet(opener, magnet)
    )

    status = qb_post(
        opener,
        "/api/v2/torrents/add",
        {
            "urls": magnet,
            "savepath": library["path"],
            "root_folder": "true",
            "paused": "true",
            "ratioLimit": "0",
            "seedingTimeLimit": "0",
        },
    )
    _require_success(
        status,
        "qBittorrent add",
    )

    torrent_hash = None
    torrent_name = None
    files = []

    for _ in range(120):
        time.sleep(0.5)

        torrents = qb_get(
            opener,
            "/api/v2/torrents/info",
        ) or []

        candidate = None

        if expected_hash:
            candidate = next(
                (
                    torrent
                    for torrent in torrents
                    if str(
                        torrent.get("hash", "")
                    ).lower() == expected_hash
                ),
                None,
            )

        if candidate is None:
            new_torrents = [
                torrent
                for torrent in torrents
                if torrent.get("hash")
                not in before_hashes
            ]

            if len(new_torrents) == 1:
                candidate = new_torrents[0]

        if not candidate:
            continue

        torrent_hash = str(
            candidate.get("hash", "")
        ).lower()
        torrent_name = candidate.get(
            "name",
            "",
        )

        if not torrent_hash:
            continue

        raw_files = qb_torrent_files(
            opener,
            torrent_hash,
        )

        if not raw_files:
            continue

        files = [
            format_qb_file(item)
            for item in raw_files
        ]

        qb_post(
            opener,
            "/api/v2/torrents/stop",
            {
                "hashes": torrent_hash,
            },
        )
        break

    if not torrent_hash:
        raise QBitTorrentError(
            (
                "Torrent został dodany, ale nie udało "
                "się odnaleźć jego metadanych"
            ),
            504,
        )

    if not files:
        try:
            qb_post(
                opener,
                "/api/v2/torrents/stop",
                {
                    "hashes": torrent_hash,
                },
            )
        except Exception:
            pass

        raise QBitTorrentError(
            (
                "Torrent został dodany, ale metadane "
                "nie zdążyły się pobrać"
            ),
            504,
            hash=torrent_hash,
        )

    return {
        "ok": True,
        "prepared": True,
        "hash": torrent_hash,
        "name": torrent_name,
        "library": library_id,
        "libraryName": library["name"],
        "files": files,
    }


def start_torrent(torrent_hash, selected):
    torrent_hash = str(
        torrent_hash or ""
    ).strip().lower()

    if not torrent_hash:
        raise QBitTorrentError(
            "Brak hash torrenta",
            400,
        )

    if not isinstance(selected, list):
        raise QBitTorrentError(
            "Nieprawidłowa lista plików",
            400,
        )

    opener = qb_client()

    _qb_step(
        opener,
        "/api/v2/torrents/stop",
        {
            "hashes": torrent_hash,
        },
        "zatrzymanie na czas konfiguracji",
    )

    torrents = qb_get(
        opener,
        "/api/v2/torrents/info?hashes="
        + urllib.parse.quote(torrent_hash),
    ) or []

    if not torrents:
        raise QBitTorrentError(
            "Nie znaleziono torrenta",
            404,
        )

    torrent = torrents[0]
    torrent_name = str(
        torrent.get("name", "")
    ).strip()
    save_path = str(
        torrent.get("save_path", "")
    ).rstrip("/")

    if not torrent_name:
        torrent_name = torrent_hash

    if not save_path:
        raise QBitTorrentError(
            "Torrent nie ma ścieżki zapisu",
            500,
        )

    safe_name = _safe_torrent_folder_name(
        torrent_name,
        torrent_hash,
    )
    torrent_folder = (
        f"{save_path}/{safe_name}"
    )

    ensure_nas_directory(torrent_folder)

    _qb_step(
        opener,
        "/api/v2/torrents/setLocation",
        {
            "hashes": torrent_hash,
            "location": torrent_folder,
        },
        "ustawienie katalogu docelowego",
    )

    location_ok = False
    actual_save_path = ""

    for _ in range(20):
        time.sleep(0.25)

        check = qb_get(
            opener,
            "/api/v2/torrents/info?hashes="
            + urllib.parse.quote(torrent_hash),
        ) or []

        if not check:
            continue

        actual_save_path = str(
            check[0].get("save_path", "")
        ).rstrip("/")

        if (
            actual_save_path
            == torrent_folder.rstrip("/")
        ):
            location_ok = True
            break

    if not location_ok:
        raise QBitTorrentError(
            (
                "qBittorrent nie przyjął nowego folderu. "
                "Pobieranie pozostaje zatrzymane."
            ),
            409,
            expected=torrent_folder,
            actual=actual_save_path,
        )

    files = qb_torrent_files(
        opener,
        torrent_hash,
    )

    if not files:
        raise QBitTorrentError(
            "Nie znaleziono plików torrenta",
            404,
        )

    valid_indexes = {
        int(item["index"])
        for item in files
        if item.get("index") is not None
    }

    try:
        selected_indexes = {
            int(index)
            for index in selected
        }
    except (TypeError, ValueError):
        raise QBitTorrentError(
            "Nieprawidłowy indeks pliku",
            400,
        )

    selected_indexes &= valid_indexes

    if not selected_indexes:
        raise QBitTorrentError(
            "Wybierz przynajmniej jeden plik",
            400,
        )

    unwanted_indexes = (
        valid_indexes - selected_indexes
    )

    if unwanted_indexes:
        _qb_step(
            opener,
            "/api/v2/torrents/filePrio",
            {
                "hash": torrent_hash,
                "id": "|".join(
                    str(index)
                    for index in sorted(
                        unwanted_indexes
                    )
                ),
                "priority": "0",
            },
            "pominięcie niezaznaczonych plików",
        )

    # Gdy zaznaczono wszystkie pliki, priorytety ustawione przez qB
    # są już prawidłowe. filePrio bywa odrzucane dla torrentów
    # jednoplikowych i nie jest wtedy potrzebne.
    if unwanted_indexes:
        _qb_step(
            opener,
            "/api/v2/torrents/filePrio",
            {
                "hash": torrent_hash,
                "id": "|".join(str(index) for index in sorted(selected_indexes)),
                "priority": "1",
            },
            "ustawienie priorytetu wybranych plików",
        )

    _qb_step(
        opener,
        "/api/v2/torrents/start",
        {
            "hashes": torrent_hash,
        },
        "wznowienie pobierania",
    )

    return {
        "ok": True,
        "hash": torrent_hash,
        "name": torrent_name,
        "folder": torrent_folder,
        "savePath": actual_save_path,
        "selected": len(selected_indexes),
        "skipped": len(unwanted_indexes),
    }


def control_torrent(torrent_hash, action):
    """Wstrzymaj/wznów albo usuń zadanie z kolejki bez kasowania plików."""
    value = str(torrent_hash or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise QBitTorrentError("Nieprawidłowy identyfikator torrenta", 400)
    if action not in ("pause", "resume", "cancel"):
        raise QBitTorrentError("Nieprawidłowa operacja torrenta", 400)
    opener = qb_client()
    torrents = qb_get(opener, "/api/v2/torrents/info?hashes=" + value) or []
    if not any(str(t.get("hash", "")).lower() == value for t in torrents):
        raise QBitTorrentError("Nie znaleziono torrenta", 404)
    path = {"pause": "/api/v2/torrents/stop", "resume": "/api/v2/torrents/start", "cancel": "/api/v2/torrents/delete"}[action]
    fields = {"hashes": value}
    if action == "cancel":
        fields["deleteFiles"] = "false"
    label = {"pause": "wstrzymanie pobierania", "resume": "wznowienie pobierania", "cancel": "usunięcie zadania bez kasowania plików"}[action]
    _qb_step(opener, path, fields, label)
    return {"ok": True, "hash": value, "action": action, "filesPreserved": action == "cancel"}
