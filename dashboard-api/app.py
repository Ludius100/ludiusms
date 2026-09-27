from flask import Flask, jsonify, request
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import shutil
import time
import uuid

from services.jellyfin import jellyfin_get

from services.qbittorrent import (
    format_qb_file,
    format_torrent,
    qb_client,
    qb_find_torrent_by_magnet,
    qb_get,
    qb_post,
    qb_torrent_files,
)

from services.activity import load_activity
from services.jellyfin_activity import start_activity_collectors

from config import (
    LOCAL_MEDIA_LIBRARIES,
    QBITTORRENT,
    QBITTORRENT_LIBRARIES,
    SUBTITLE_EXTENSIONS,
    SUBTITLE_LANGUAGE_TAGS,
    UPLOAD_CHUNK_MAX,
    UPLOAD_STAGING_DIR,
    UPLOAD_STATE_DIR,
    VIDEO_EXTENSIONS,
)

app = Flask(__name__)


# ============================================================
# Background collectors
# ============================================================

start_activity_collectors()


# ============================================================
# System
# ============================================================

def cpu_snapshot():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]

    values = list(map(int, parts))

    idle = values[3] + values[4]
    total = sum(values)

    return idle, total


def cpu_percent():
    idle1, total1 = cpu_snapshot()
    time.sleep(0.15)
    idle2, total2 = cpu_snapshot()

    idle_delta = idle2 - idle1
    total_delta = total2 - total1

    if total_delta == 0:
        return 0

    return round(
        100 * (1 - idle_delta / total_delta)
    )


def check_http(url):
    start = time.monotonic()

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NAS-Dashboard/1.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=3
        ) as response:
            status = response.status

        latency = round(
            (time.monotonic() - start) * 1000
        )

        return {
            "online": 200 <= status < 500,
            "latency": latency
        }

    except Exception:
        return {
            "online": False,
            "latency": None
        }


# ============================================================
# API
# ============================================================


@app.route("/api/activity")
def activity():
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20

    limit = max(1, min(limit, 100))

    return jsonify({
        "events": load_activity()[:limit]
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/api/jellyfin")
def jellyfin():
    try:
        counts = jellyfin_get("/Items/Counts")
        sessions = jellyfin_get("/Sessions")

        active_sessions = sum(
            1 for session in sessions
            if session.get("NowPlayingItem")
        )

        return jsonify({
            "online": True,
            "movies": counts.get("MovieCount", 0),
            "series": counts.get("SeriesCount", 0),
            "episodes": counts.get("EpisodeCount", 0),
            "songs": counts.get("SongCount", 0),
            "activeSessions": active_sessions
        })

    except Exception as e:
        print("Jellyfin API error:", e)

        return jsonify({
            "online": False
        }), 503


@app.route("/api/system")
def system_stats():
    try:
        mem = {}

        with open("/proc/meminfo") as f:
            for line in f:
                key, value = line.split(":", 1)

                mem[key] = int(
                    value.strip().split()[0]
                )

        ram_percent = round(
            (
                1 -
                mem["MemAvailable"] /
                mem["MemTotal"]
            ) * 100
        )

        with open("/proc/uptime") as f:
            uptime_seconds = int(
                float(f.read().split()[0])
            )

        disk = shutil.disk_usage("/nas")

        disk_percent = round(
            disk.used / disk.total * 100
        )

        return jsonify({
            "cpu": cpu_percent(),
            "ram": ram_percent,

            "disk": disk_percent,

            "diskUsedGB": round(
                disk.used / 1024**3,
                1
            ),

            "diskTotalGB": round(
                disk.total / 1024**3,
                1
            ),

            "uptimeSeconds": uptime_seconds
        })

    except Exception as e:
        print("System API error:", e)

        return jsonify({
            "error": "System stats unavailable"
        }), 503


@app.route("/api/status")
def status():
    services = {
        "jellyfin": "http://127.0.0.1:8096",
        "gdrive": "http://100.127.67.28:8088",
        "kuma": "http://100.127.67.28:3001",
        "ntfy": "http://100.127.67.28:8089",
        "qbittorrent": QBITTORRENT
    }

    result = {}

    for name, url in services.items():
        result[name] = check_http(url)

    return jsonify(result)


@app.route("/api/qbittorrent/libraries")
def qbittorrent_libraries():
    return jsonify({
        "libraries": [
            {
                "id": library_id,
                "name": library["name"]
            }
            for library_id, library
            in QBITTORRENT_LIBRARIES.items()
        ]
    })


@app.route("/api/qbittorrent")
def qbittorrent_status():
    try:
        opener = qb_client()

        transfer = qb_get(
            opener,
            "/api/v2/transfer/info"
        )

        torrents = qb_get(
            opener,
            "/api/v2/torrents/info"
        )

        torrents = torrents or []

        formatted = [
            format_torrent(torrent)
            for torrent in torrents
        ]

        active = [
            torrent
            for torrent in formatted
            if torrent["state"] not in (
                "pausedDL",
                "pausedUP",
                "stoppedDL",
                "stoppedUP",
                "error",
                "missingFiles"
            )
        ]

        downloading = [
            torrent
            for torrent in formatted
            if torrent["state"] in (
                "downloading",
                "metaDL",
                "forcedDL",
                "stalledDL",
                "checkingDL",
                "allocating"
            )
        ]

        return jsonify({
            "online": True,

            "downloadSpeed": transfer.get(
                "dl_info_speed",
                0
            ),

            "uploadSpeed": transfer.get(
                "up_info_speed",
                0
            ),

            "downloaded": transfer.get(
                "dl_info_data",
                0
            ),

            "uploaded": transfer.get(
                "up_info_data",
                0
            ),

            "total": len(formatted),
            "active": len(active),
            "downloading": len(downloading),

            "torrents": formatted
        })

    except Exception as e:
        print(
            "qBittorrent API error:",
            type(e).__name__,
            e
        )

        return jsonify({
            "online": False,
            "error": "qBittorrent unavailable"
        }), 503


@app.route(
    "/api/qbittorrent/add",
    methods=["POST", "OPTIONS"]
)
def qbittorrent_add():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json(silent=True) or {}

        magnet = str(data.get("magnet", "")).strip()

        if not magnet:
            return jsonify({
                "ok": False,
                "error": "Brak linku magnet"
            }), 400

        if not magnet.lower().startswith("magnet:?"):
            return jsonify({
                "ok": False,
                "error": "Dozwolone są tylko linki magnet"
            }), 400

        if len(magnet) > 16_384:
            return jsonify({
                "ok": False,
                "error": "Link magnet jest zbyt długi"
            }), 400

        library_id = str(
            data.get("library", "downloads")
        ).strip()

        library = QBITTORRENT_LIBRARIES.get(library_id)

        if not library:
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa biblioteka"
            }), 400

        opener = qb_client()

        before = qb_get(
            opener,
            "/api/v2/torrents/info"
        ) or []

        before_hashes = {
            t.get("hash")
            for t in before
            if t.get("hash")
        }

        expected_hash = qb_find_torrent_by_magnet(
            opener,
            magnet
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
                "seedingTimeLimit": "0"
            }
        )

        if status not in (200, 204):
            raise RuntimeError(
                f"qBittorrent add HTTP {status}"
            )

        torrent_hash = None
        torrent_name = None
        files = []

        # Czekamy maksymalnie ~60 s na metadane.
        for _ in range(120):
            time.sleep(0.5)

            torrents = qb_get(
                opener,
                "/api/v2/torrents/info"
            ) or []

            candidate = None

            if expected_hash:
                candidate = next(
                    (
                        t for t in torrents
                        if str(
                            t.get("hash", "")
                        ).lower() == expected_hash
                    ),
                    None
                )

            if candidate is None:
                new_torrents = [
                    t for t in torrents
                    if t.get("hash") not in before_hashes
                ]

                if len(new_torrents) == 1:
                    candidate = new_torrents[0]

            if not candidate:
                continue

            torrent_hash = str(
                candidate.get("hash", "")
            ).lower()

            torrent_name = candidate.get("name", "")

            if not torrent_hash:
                continue

            raw_files = qb_torrent_files(
                opener,
                torrent_hash
            )

            if not raw_files:
                continue

            files = [
                format_qb_file(item)
                for item in raw_files
            ]

            # Mamy już metadane. Teraz jawnie STOP,
            # zanim użytkownik wybierze pliki.
            qb_post(
                opener,
                "/api/v2/torrents/stop",
                {
                    "hashes": torrent_hash
                }
            )

            break

        if not torrent_hash:
            return jsonify({
                "ok": False,
                "error": (
                    "Torrent został dodany, ale nie udało "
                    "się odnaleźć jego metadanych"
                )
            }), 504

        if not files:
            # Jeżeli znamy hash, zatrzymaj torrent również
            # w przypadku timeoutu metadanych.
            try:
                qb_post(
                    opener,
                    "/api/v2/torrents/stop",
                    {
                        "hashes": torrent_hash
                    }
                )
            except Exception:
                pass

            return jsonify({
                "ok": False,
                "hash": torrent_hash,
                "error": (
                    "Torrent został dodany, ale metadane "
                    "nie zdążyły się pobrać"
                )
            }), 504

        return jsonify({
            "ok": True,
            "prepared": True,
            "hash": torrent_hash,
            "name": torrent_name,
            "library": library_id,
            "libraryName": library["name"],
            "files": files
        })

    except Exception as e:
        print(
            "qBittorrent prepare error:",
            type(e).__name__,
            e,
            flush=True
        )

        return jsonify({
            "ok": False,
            "error": "Nie udało się przygotować magnetu"
        }), 503


@app.route(
    "/api/qbittorrent/start",
    methods=["POST", "OPTIONS"]
)
def qbittorrent_start():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json(silent=True) or {}

        torrent_hash = str(
            data.get("hash", "")
        ).strip().lower()

        selected = data.get("selected", [])

        if not torrent_hash:
            return jsonify({
                "ok": False,
                "error": "Brak hash torrenta"
            }), 400

        if not isinstance(selected, list):
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa lista plików"
            }), 400

        opener = qb_client()

        # Na wszelki wypadek zatrzymujemy torrent ponownie.
        qb_post(
            opener,
            "/api/v2/torrents/stop",
            {
                "hashes": torrent_hash
            }
        )

        torrents = qb_get(
            opener,
            "/api/v2/torrents/info?hashes="
            + urllib.parse.quote(torrent_hash)
        ) or []

        if not torrents:
            return jsonify({
                "ok": False,
                "error": "Nie znaleziono torrenta"
            }), 404

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
            return jsonify({
                "ok": False,
                "error": "Torrent nie ma ścieżki zapisu"
            }), 500

        safe_name = torrent_name

        for char in '<>:"/\\|?*':
            safe_name = safe_name.replace(char, "_")

        safe_name = safe_name.strip(" .")

        if not safe_name:
            safe_name = torrent_hash

        torrent_folder = f"{save_path}/{safe_name}"

        # Fizycznie tworzymy katalog.
        os.makedirs(
            torrent_folder,
            exist_ok=True
        )

        # qBittorrent działa jako nas:nasdata (1002:1003).
        # Folder musi być dla niego zapisywalny.
        os.chown(torrent_folder, 1002, 1003)
        os.chmod(torrent_folder, 0o2770)

        # Dopiero teraz qBittorrent może go przyjąć.
        status = qb_post(
            opener,
            "/api/v2/torrents/setLocation",
            {
                "hashes": torrent_hash,
                "location": torrent_folder
            }
        )

        if status not in (200, 204):
            raise RuntimeError(
                f"setLocation HTTP {status}"
            )

        # Sprawdzamy, czy qBittorrent NAPRAWDĘ
        # zaakceptował nową lokalizację.
        location_ok = False
        actual_save_path = ""

        for _ in range(20):
            time.sleep(0.25)

            check = qb_get(
                opener,
                "/api/v2/torrents/info?hashes="
                + urllib.parse.quote(torrent_hash)
            ) or []

            if not check:
                continue

            actual_save_path = str(
                check[0].get("save_path", "")
            ).rstrip("/")

            if actual_save_path == torrent_folder.rstrip("/"):
                location_ok = True
                break

        if not location_ok:
            return jsonify({
                "ok": False,
                "error": (
                    "qBittorrent nie przyjął nowego folderu. "
                    "Pobieranie pozostaje zatrzymane."
                ),
                "expected": torrent_folder,
                "actual": actual_save_path
            }), 409

        files = qb_torrent_files(
            opener,
            torrent_hash
        )

        if not files:
            return jsonify({
                "ok": False,
                "error": "Nie znaleziono plików torrenta"
            }), 404

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
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowy indeks pliku"
            }), 400

        selected_indexes &= valid_indexes

        if not selected_indexes:
            return jsonify({
                "ok": False,
                "error": "Wybierz przynajmniej jeden plik"
            }), 400

        unwanted_indexes = (
            valid_indexes - selected_indexes
        )

        if unwanted_indexes:
            qb_post(
                opener,
                "/api/v2/torrents/filePrio",
                {
                    "hash": torrent_hash,
                    "id": "|".join(
                        str(i)
                        for i in sorted(unwanted_indexes)
                    ),
                    "priority": "0"
                }
            )

        qb_post(
            opener,
            "/api/v2/torrents/filePrio",
            {
                "hash": torrent_hash,
                "id": "|".join(
                    str(i)
                    for i in sorted(selected_indexes)
                ),
                "priority": "1"
            }
        )

        # Dopiero TERAZ pozwalamy pobierać.
        status = qb_post(
            opener,
            "/api/v2/torrents/start",
            {
                "hashes": torrent_hash
            }
        )

        if status not in (200, 204):
            raise RuntimeError(
                f"start HTTP {status}"
            )

        return jsonify({
            "ok": True,
            "hash": torrent_hash,
            "name": torrent_name,
            "folder": torrent_folder,
            "savePath": actual_save_path,
            "selected": len(selected_indexes),
            "skipped": len(unwanted_indexes)
        })

    except Exception as e:
        print(
            "qBittorrent start error:",
            type(e).__name__,
            e,
            flush=True
        )

        return jsonify({
            "ok": False,
            "error": "Nie udało się uruchomić torrenta"
        }), 503


# ============================================================
# Local Media Upload
# ============================================================

def safe_media_component(value, fallback="media"):
    """Return one safe filesystem path component while keeping Unicode names."""
    value = str(value or "").strip()
    cleaned = []

    for char in value:
        if char in '/\\' or ord(char) < 32:
            cleaned.append("_")
        elif char in '<>:"|?*':
            cleaned.append("_")
        else:
            cleaned.append(char)

    value = "".join(cleaned).strip(" .")

    if value in ("", ".", ".."):
        value = fallback

    return value[:180]


def path_is_inside(child, parent):
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)

    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False


def set_nas_permissions(path):
    os.chown(path, 1002, 1003)

    if os.path.isdir(path):
        os.chmod(path, 0o2770)
    else:
        os.chmod(path, 0o660)


def upload_state_path(upload_id):
    upload_id = str(upload_id or "").strip().lower()

    if len(upload_id) != 32 or any(c not in "0123456789abcdef" for c in upload_id):
        raise ValueError("Nieprawidłowe ID uploadu")

    return os.path.join(UPLOAD_STATE_DIR, upload_id + ".json")


def load_upload_state(upload_id):
    path = upload_state_path(upload_id)

    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)

    if not isinstance(state, dict):
        raise ValueError("Uszkodzony stan uploadu")

    return state


def save_upload_state(state):
    os.makedirs(UPLOAD_STATE_DIR, exist_ok=True)
    path = upload_state_path(state["id"])
    temporary = path + ".tmp"

    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    os.replace(temporary, path)


def delete_upload_state(upload_id):
    try:
        os.remove(upload_state_path(upload_id))
    except FileNotFoundError:
        pass


def public_upload_state(state):
    staging_path = state["stagingPath"]
    received = os.path.getsize(staging_path) if os.path.exists(staging_path) else 0
    expected = int(state["size"])

    return {
        "ok": True,
        "uploadId": state["id"],
        "library": state["library"],
        "libraryName": state["libraryName"],
        "folder": state["folder"],
        "originalName": state["originalName"],
        "name": state["name"],
        "size": expected,
        "received": received,
        "remaining": max(0, expected - received),
        "complete": received == expected,
        "chunkMax": UPLOAD_CHUNK_MAX
    }


def prepare_upload_target(data):
    library_id = str(data.get("library", "")).strip()
    library = LOCAL_MEDIA_LIBRARIES.get(library_id)

    if not library:
        raise ValueError("Nieprawidłowa biblioteka lokalnych mediów")

    raw_folder = str(data.get("folder", "") or "").replace("\\", "/").strip("/")
    folder_parts = []

    for part in raw_folder.split("/"):
        if not part or part in (".", ".."):
            continue
        folder_parts.append(safe_media_component(part, "media"))

    if not folder_parts:
        folder_parts = ["Nowe media"]

    folder_name = "/".join(folder_parts)
    original_name = safe_media_component(data.get("originalName", ""), "media.bin")
    target_name = safe_media_component(data.get("targetName") or original_name, original_name)

    try:
        size = int(data.get("size"))
    except (TypeError, ValueError):
        raise ValueError("Nieprawidłowy rozmiar pliku")

    if size < 0:
        raise ValueError("Nieprawidłowy rozmiar pliku")

    library_root = os.path.realpath(library["path"])
    destination_dir = os.path.join(library_root, *folder_parts)
    destination = os.path.join(destination_dir, target_name)

    if not path_is_inside(destination_dir, library_root):
        raise ValueError("Nieprawidłowa ścieżka docelowa")

    if not path_is_inside(destination, library_root):
        raise ValueError("Nieprawidłowa nazwa pliku")

    return library_id, library, folder_name, original_name, target_name, size, destination_dir, destination



# ============================================================
# Media Planner / Waiting Room
# ============================================================

def split_media_filename(name):
    clean = safe_media_component(
        os.path.basename(str(name or "").replace("\\", "/")),
        "media.bin"
    )
    stem, ext = os.path.splitext(clean)
    return clean, stem, ext.lower()


def subtitle_base_and_suffix(stem):
    """
    "episode.pol" -> ("episode", ".pol")
    "episode"     -> ("episode", "")
    """
    parts = stem.split(".")

    if len(parts) > 1 and parts[-1].lower() in SUBTITLE_LANGUAGE_TAGS:
        return ".".join(parts[:-1]), "." + parts[-1]

    return stem, ""


def planner_target(library, relative_parts):
    root = os.path.realpath(library["path"])
    target = os.path.join(root, *relative_parts)

    if not path_is_inside(target, root):
        raise ValueError("Nieprawidłowa ścieżka docelowa")

    return target


def planner_item(original, target_name, target_path, size=0, kind="other",
                 season=None, episode=None, paired_with=None):
    conflict = os.path.exists(target_path)

    result = {
        "originalName": original,
        "targetName": target_name,
        "targetPath": target_path,
        "size": int(size or 0),
        "kind": kind,
        "status": "conflict" if conflict else "ok",
        "conflict": conflict
    }

    if season is not None:
        result["season"] = int(season)

    if episode is not None:
        result["episode"] = int(episode)

    if paired_with is not None:
        result["pairedWith"] = paired_with

    return result


def plan_movie(data, library_id, library, files):
    if library_id not in ("movies", "animeMovies"):
        raise ValueError("Film może trafić tylko do Filmy lub Anime Filmy")

    title = safe_media_component(data.get("title", ""), "")
    if not title:
        raise ValueError("Podaj tytuł filmu")

    year = data.get("year")
    if year not in (None, ""):
        try:
            year = int(year)
        except (TypeError, ValueError):
            raise ValueError("Nieprawidłowy rok filmu")

        if year < 1888 or year > 2200:
            raise ValueError("Nieprawidłowy rok filmu")
    else:
        year = None

    folder = f"{title} ({year})" if year else title
    folder = safe_media_component(folder, title)

    planned = []

    for file_info in files:
        original, stem, ext = split_media_filename(file_info.get("name"))
        size = file_info.get("size", 0)

        if ext in VIDEO_EXTENSIONS:
            target_name = original
            kind = "video"
        elif ext in SUBTITLE_EXTENSIONS:
            target_name = original
            kind = "subtitle"
        else:
            target_name = original
            kind = "other"

        target_path = planner_target(library, [folder, target_name])
        planned.append(
            planner_item(
                original, target_name, target_path,
                size=size, kind=kind
            )
        )

    return {
        "mediaType": "movie",
        "title": title,
        "year": year,
        "folder": folder,
        "items": planned
    }


def plan_series(data, library_id, library, files):
    if library_id not in ("series", "anime"):
        raise ValueError("Serial może trafić tylko do Seriale lub Anime")

    title = safe_media_component(data.get("title", ""), "")
    if not title:
        raise ValueError("Podaj tytuł serialu")

    try:
        default_season = int(data.get("season", 1))
        first_episode = int(data.get("firstEpisode", 1))
    except (TypeError, ValueError):
        raise ValueError("Nieprawidłowy sezon lub numer pierwszego odcinka")

    if default_season < 0 or default_season > 999:
        raise ValueError("Nieprawidłowy numer sezonu")

    if first_episode < 0 or first_episode > 9999:
        raise ValueError("Nieprawidłowy numer pierwszego odcinka")

    videos = []
    subtitles = []
    ignored = []

    for position, file_info in enumerate(files):
        original, stem, ext = split_media_filename(file_info.get("name"))
        normalized = {
            "position": position,
            "original": original,
            "stem": stem,
            "ext": ext,
            "size": file_info.get("size", 0),
            "season": file_info.get("season"),
            "episode": file_info.get("episode")
        }

        if ext in VIDEO_EXTENSIONS:
            videos.append(normalized)
        elif ext in SUBTITLE_EXTENSIONS:
            subtitles.append(normalized)
        else:
            ignored.append(normalized)

    if not videos:
        raise ValueError("Nie znaleziono żadnego pliku wideo")

    # Numery odcinków nadajemy w kolejności przekazanej przez poczekalnię.
    for index, video in enumerate(videos):
        try:
            season = (
                int(video["season"])
                if video["season"] not in (None, "")
                else default_season
            )
            episode = (
                int(video["episode"])
                if video["episode"] not in (None, "")
                else first_episode + index
            )
        except (TypeError, ValueError):
            raise ValueError("Nieprawidłowy sezon lub numer odcinka przy pliku " + video["original"])

        if season < 0 or season > 999 or episode < 0 or episode > 9999:
            raise ValueError("Nieprawidłowy sezon lub numer odcinka przy pliku " + video["original"])

        video["targetSeason"] = season
        video["targetEpisode"] = episode

    planned = []
    video_by_stem = {video["stem"].lower(): video for video in videos}

    for video in videos:
        season = video["targetSeason"]
        episode = video["targetEpisode"]
        season_folder = f"Season {season:02d}"
        base = f"{title} S{season:02d}E{episode:02d}"
        target_name = base + video["ext"]
        target_path = planner_target(
            library,
            [title, season_folder, target_name]
        )

        planned.append(
            planner_item(
                video["original"], target_name, target_path,
                size=video["size"], kind="video",
                season=season, episode=episode
            )
        )

    # Napisy próbujemy przypisać po nazwie bazowej pliku.
    for subtitle in subtitles:
        base_stem, language_suffix = subtitle_base_and_suffix(subtitle["stem"])
        paired = video_by_stem.get(base_stem.lower())

        if paired is None:
            # Nie zgadujemy numeru odcinka. Poczekalnia pokaże "check".
            planned.append({
                "originalName": subtitle["original"],
                "targetName": None,
                "targetPath": None,
                "size": int(subtitle["size"] or 0),
                "kind": "subtitle",
                "status": "check",
                "conflict": False,
                "reason": "Nie udało się jednoznacznie przypisać napisów do odcinka"
            })
            continue

        season = paired["targetSeason"]
        episode = paired["targetEpisode"]
        season_folder = f"Season {season:02d}"
        base = f"{title} S{season:02d}E{episode:02d}"
        target_name = base + language_suffix + subtitle["ext"]
        target_path = planner_target(
            library,
            [title, season_folder, target_name]
        )

        planned.append(
            planner_item(
                subtitle["original"], target_name, target_path,
                size=subtitle["size"], kind="subtitle",
                season=season, episode=episode,
                paired_with=paired["original"]
            )
        )

    for item in ignored:
        planned.append({
            "originalName": item["original"],
            "targetName": None,
            "targetPath": None,
            "size": int(item["size"] or 0),
            "kind": "other",
            "status": "ignored",
            "conflict": False,
            "reason": "Nieobsługiwany typ pliku"
        })

    return {
        "mediaType": "series",
        "title": title,
        "season": default_season,
        "firstEpisode": first_episode,
        "folder": title,
        "items": planned
    }


def build_plan_tree(library, result):
    root = library["name"]
    paths = []

    for item in result["items"]:
        target = item.get("targetPath")
        if not target:
            continue

        relative = os.path.relpath(target, library["path"])
        paths.append(relative.replace(os.sep, "/"))

    return {
        "root": root,
        "paths": paths
    }




@app.route("/api/media/titles", methods=["GET", "OPTIONS"])
def media_titles():
    if request.method == "OPTIONS":
        return "", 204

    try:
        library_id = str(request.args.get("library", "")).strip()
        library = LOCAL_MEDIA_LIBRARIES.get(library_id)

        if library_id not in ("movies", "animeMovies", "series", "anime") or not library:
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa biblioteka lokalnych mediów"
            }), 400

        root = os.path.realpath(library["path"])
        titles = []

        if os.path.isdir(root):
            with os.scandir(root) as entries:
                for entry in entries:
                    if entry.name.startswith("."):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            titles.append(entry.name)
                    except OSError:
                        continue

        titles.sort(key=lambda value: value.casefold())

        return jsonify({
            "ok": True,
            "library": library_id,
            "libraryName": library["name"],
            "titles": titles
        })

    except Exception as e:
        print("Media titles error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się odczytać listy tytułów"
        }), 500


@app.route("/api/media/last-episode", methods=["GET", "OPTIONS"])
def media_last_episode():
    if request.method == "OPTIONS":
        return "", 204

    try:
        library_id = str(request.args.get("library", "")).strip()
        title = str(request.args.get("title", "")).strip()

        try:
            season = int(request.args.get("season", 1))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Nieprawidłowy sezon"}), 400

        library = LOCAL_MEDIA_LIBRARIES.get(library_id)

        if library_id not in ("series", "anime") or not library:
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa biblioteka seriali"
            }), 400

        if not title:
            return jsonify({
                "ok": False,
                "error": "Brak tytułu"
            }), 400

        library_root = os.path.realpath(library["path"])

        # Tytuł musi być prawdziwym folderem bezpośrednio w bibliotece.
        title_dir = None

        if os.path.isdir(library_root):
            with os.scandir(library_root) as entries:
                for entry in entries:
                    try:
                        if (
                            entry.is_dir(follow_symlinks=False)
                            and entry.name.casefold() == title.casefold()
                        ):
                            title_dir = os.path.realpath(entry.path)
                            break
                    except OSError:
                        continue

        if title_dir is None:
            return jsonify({
                "ok": True,
                "exists": False,
                "season": season,
                "lastEpisode": None,
                "nextEpisode": 1
            })

        if not path_is_inside(title_dir, library_root):
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa ścieżka tytułu"
            }), 400

        import re

        episode_pattern = re.compile(
            r"(?i)(?:^|[^A-Z0-9])S(\d{1,3})E(\d{1,4})(?:[^0-9]|$)"
        )

        video_extensions = {
            ".mkv", ".mp4", ".avi", ".m4v",
            ".mov", ".ts", ".m2ts", ".webm"
        }

        highest_episode = None
        highest_file = None

        for current_root, dirs, files in os.walk(title_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in files:
                extension = os.path.splitext(filename)[1].lower()

                if extension not in video_extensions:
                    continue

                match = episode_pattern.search(filename)

                if not match:
                    continue

                file_season = int(match.group(1))
                episode = int(match.group(2))

                if file_season != season:
                    continue

                if highest_episode is None or episode > highest_episode:
                    highest_episode = episode
                    highest_file = filename

        return jsonify({
            "ok": True,
            "exists": True,
            "season": season,
            "lastEpisode": highest_episode,
            "lastFile": highest_file,
            "nextEpisode": (
                highest_episode + 1
                if highest_episode is not None
                else 1
            )
        })

    except Exception as exc:
        print(
            "media_last_episode:",
            type(exc).__name__,
            str(exc),
            flush=True
        )

        return jsonify({
            "ok": False,
            "error": "Nie udało się sprawdzić ostatniego odcinka"
        }), 500


@app.route("/api/media/plan", methods=["POST", "OPTIONS"])
def media_plan():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json(silent=True) or {}
        media_type = str(data.get("type", "")).strip().lower()
        library_id = str(data.get("library", "")).strip()
        library = LOCAL_MEDIA_LIBRARIES.get(library_id)
        files = data.get("files", [])

        if not library:
            return jsonify({
                "ok": False,
                "error": "Nieprawidłowa biblioteka lokalnych mediów"
            }), 400

        if not isinstance(files, list) or not files:
            return jsonify({
                "ok": False,
                "error": "Nie wybrano żadnych plików"
            }), 400

        if len(files) > 5000:
            return jsonify({
                "ok": False,
                "error": "Za dużo plików w jednym planie"
            }), 413

        normalized_files = []
        for item in files:
            if not isinstance(item, dict):
                return jsonify({
                    "ok": False,
                    "error": "Nieprawidłowa lista plików"
                }), 400

            name = str(item.get("name", "")).strip()
            if not name:
                return jsonify({
                    "ok": False,
                    "error": "Jeden z plików nie ma nazwy"
                }), 400

            normalized_files.append(item)

        if media_type == "movie":
            result = plan_movie(
                data, library_id, library, normalized_files
            )
        elif media_type == "series":
            result = plan_series(
                data, library_id, library, normalized_files
            )
        else:
            return jsonify({
                "ok": False,
                "error": "Typ musi być movie albo series"
            }), 400

        conflicts = sum(
            1 for item in result["items"]
            if item.get("status") == "conflict"
        )
        checks = sum(
            1 for item in result["items"]
            if item.get("status") == "check"
        )

        result.update({
            "ok": True,
            "library": library_id,
            "libraryName": library["name"],
            "conflicts": conflicts,
            "needsCheck": checks,
            "ready": conflicts == 0 and checks == 0,
            "tree": build_plan_tree(library, result)
        })

        return jsonify(result)

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        print("Media planner error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się przygotować planu mediów"
        }), 500


@app.route("/api/media/upload/init", methods=["POST", "OPTIONS"])
def media_upload_init():
    if request.method == "OPTIONS":
        return "", 204

    try:
        data = request.get_json(silent=True) or {}
        (
            library_id, library, folder_name, original_name,
            target_name, size, destination_dir, destination
        ) = prepare_upload_target(data)

        if os.path.exists(destination):
            return jsonify({
                "ok": False,
                "error": "Plik docelowy już istnieje",
                "conflict": True,
                "target": destination
            }), 409

        os.makedirs(UPLOAD_STAGING_DIR, exist_ok=True)
        set_nas_permissions(UPLOAD_STAGING_DIR)

        upload_id = uuid.uuid4().hex
        staging_path = os.path.join(UPLOAD_STAGING_DIR, upload_id + ".part")

        with open(staging_path, "xb"):
            pass
        set_nas_permissions(staging_path)

        state = {
            "id": upload_id,
            "library": library_id,
            "libraryName": library["name"],
            "folder": folder_name,
            "originalName": original_name,
            "name": target_name,
            "size": size,
            "destinationDir": destination_dir,
            "destination": destination,
            "stagingPath": staging_path,
            "createdAt": int(time.time())
        }
        save_upload_state(state)

        return jsonify(public_upload_state(state)), 201

    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        print("Upload init error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się utworzyć sesji uploadu"}), 500


@app.route("/api/media/upload/<upload_id>", methods=["GET", "OPTIONS"])
def media_upload_status(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        state = load_upload_state(upload_id)
        return jsonify(public_upload_state(state))
    except (FileNotFoundError, ValueError):
        return jsonify({"ok": False, "error": "Nie znaleziono sesji uploadu"}), 404
    except Exception as e:
        print("Upload status error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się odczytać uploadu"}), 500


@app.route("/api/media/upload/<upload_id>/chunk", methods=["POST", "OPTIONS"])
def media_upload_chunk(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        state = load_upload_state(upload_id)
        staging_path = state["stagingPath"]
        expected_size = int(state["size"])

        try:
            offset = int(request.headers.get("X-Upload-Offset", ""))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Brak lub błędny X-Upload-Offset"}), 400

        current_size = os.path.getsize(staging_path)

        if offset != current_size:
            return jsonify({
                "ok": False,
                "error": "Offset nie zgadza się ze stanem serwera",
                "expectedOffset": current_size
            }), 409

        content_length = request.content_length
        if content_length is not None and content_length > UPLOAD_CHUNK_MAX:
            return jsonify({
                "ok": False,
                "error": "Chunk jest zbyt duży",
                "chunkMax": UPLOAD_CHUNK_MAX
            }), 413

        remaining = expected_size - current_size
        if remaining <= 0:
            return jsonify(public_upload_state(state))

        written = 0
        with open(staging_path, "ab") as f:
            while True:
                block = request.stream.read(min(1024 * 1024, UPLOAD_CHUNK_MAX - written + 1))
                if not block:
                    break

                written += len(block)
                if written > UPLOAD_CHUNK_MAX or written > remaining:
                    f.truncate(current_size)
                    return jsonify({
                        "ok": False,
                        "error": "Chunk przekracza dozwolony rozmiar uploadu"
                    }), 413

                f.write(block)

            f.flush()
            os.fsync(f.fileno())

        set_nas_permissions(staging_path)
        result = public_upload_state(state)
        result["written"] = written
        return jsonify(result)

    except (FileNotFoundError, ValueError):
        return jsonify({"ok": False, "error": "Nie znaleziono sesji uploadu"}), 404
    except Exception as e:
        print("Upload chunk error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się zapisać części pliku"}), 500


@app.route("/api/media/upload/<upload_id>/finalize", methods=["POST", "OPTIONS"])
def media_upload_finalize(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        state = load_upload_state(upload_id)
        staging_path = state["stagingPath"]
        destination_dir = state["destinationDir"]
        destination = state["destination"]
        expected_size = int(state["size"])

        if not os.path.exists(staging_path):
            return jsonify({"ok": False, "error": "Brak pliku tymczasowego"}), 409

        received = os.path.getsize(staging_path)
        if received != expected_size:
            return jsonify({
                "ok": False,
                "error": "Upload nie jest kompletny",
                "received": received,
                "size": expected_size
            }), 409

        if os.path.exists(destination):
            return jsonify({
                "ok": False,
                "error": "Plik docelowy już istnieje",
                "conflict": True,
                "target": destination
            }), 409

        os.makedirs(destination_dir, exist_ok=True)
        set_nas_permissions(destination_dir)

        # Final conflict check immediately before the atomic move.
        if os.path.exists(destination):
            return jsonify({
                "ok": False,
                "error": "Plik docelowy pojawił się podczas uploadu",
                "conflict": True,
                "target": destination
            }), 409

        os.replace(staging_path, destination)
        set_nas_permissions(destination)
        delete_upload_state(upload_id)

        return jsonify({
            "ok": True,
            "uploadId": upload_id,
            "library": state["library"],
            "libraryName": state["libraryName"],
            "folder": state["folder"],
            "originalName": state["originalName"],
            "name": state["name"],
            "path": destination,
            "size": os.path.getsize(destination)
        })

    except (FileNotFoundError, ValueError):
        return jsonify({"ok": False, "error": "Nie znaleziono sesji uploadu"}), 404
    except Exception as e:
        print("Upload finalize error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się zakończyć uploadu"}), 500


@app.route("/api/media/upload/<upload_id>", methods=["DELETE", "OPTIONS"])
def media_upload_cancel(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        state = load_upload_state(upload_id)
        staging_path = state["stagingPath"]

        if os.path.exists(staging_path):
            os.remove(staging_path)

        delete_upload_state(upload_id)
        return jsonify({"ok": True, "cancelled": True, "uploadId": upload_id})

    except (FileNotFoundError, ValueError):
        return jsonify({"ok": False, "error": "Nie znaleziono sesji uploadu"}), 404
    except Exception as e:
        print("Upload cancel error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się anulować uploadu"}), 500


@app.route("/api/media/upload", methods=["POST", "OPTIONS"])
def media_upload():
    """Small-file fallback/test uploader. Large browser uploads use sessions above."""
    if request.method == "OPTIONS":
        return "", 204

    temporary_path = None

    try:
        library_id = str(request.form.get("library", "")).strip()
        library = LOCAL_MEDIA_LIBRARIES.get(library_id)

        if not library:
            return jsonify({"ok": False, "error": "Nieprawidłowa biblioteka lokalnych mediów"}), 400

        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"ok": False, "error": "Nie wybrano pliku"}), 400

        folder_name = safe_media_component(request.form.get("folder", ""), "Nowe media")
        original_name = safe_media_component(os.path.basename(str(upload.filename).replace("\\", "/")), "media.bin")
        target_name = safe_media_component(request.form.get("targetName") or original_name, original_name)

        library_root = os.path.realpath(library["path"])
        destination_dir = os.path.join(library_root, folder_name)
        destination = os.path.join(destination_dir, target_name)

        if not path_is_inside(destination_dir, library_root) or not path_is_inside(destination, library_root):
            return jsonify({"ok": False, "error": "Nieprawidłowa ścieżka docelowa"}), 400

        if os.path.exists(destination):
            return jsonify({"ok": False, "error": "Plik docelowy już istnieje", "conflict": True, "target": destination}), 409

        os.makedirs(destination_dir, exist_ok=True)
        set_nas_permissions(destination_dir)
        temporary_path = os.path.join(destination_dir, ".upload-" + uuid.uuid4().hex + ".part")

        upload.save(temporary_path)
        set_nas_permissions(temporary_path)

        if os.path.exists(destination):
            os.remove(temporary_path)
            temporary_path = None
            return jsonify({"ok": False, "error": "Plik docelowy pojawił się podczas uploadu", "conflict": True, "target": destination}), 409

        os.replace(temporary_path, destination)
        temporary_path = None
        set_nas_permissions(destination)

        return jsonify({
            "ok": True,
            "library": library_id,
            "libraryName": library["name"],
            "folder": folder_name,
            "originalName": original_name,
            "name": target_name,
            "path": destination,
            "size": os.path.getsize(destination)
        })

    except Exception as e:
        print("Local media upload error:", type(e).__name__, e, flush=True)

        if temporary_path:
            try:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)
            except Exception:
                pass

        return jsonify({"ok": False, "error": "Nie udało się przesłać pliku"}), 500


@app.after_request
def cors(response):
    origin = os.environ.get(
        "HOMEPAGE_ORIGIN",
        "http://100.127.67.28:3000"
    )

    response.headers[
        "Access-Control-Allow-Origin"
    ] = origin

    response.headers[
        "Access-Control-Allow-Methods"
    ] = "GET, POST, DELETE, OPTIONS"

    response.headers[
        "Access-Control-Allow-Headers"
    ] = "Content-Type, X-Upload-Offset"

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8090
    )