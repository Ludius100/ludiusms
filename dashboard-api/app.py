from flask import Flask, jsonify, request
import urllib.parse
import urllib.error
import os
import time

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
from services.system import check_http, get_system_stats
from services.media_paths import path_is_inside
from services.media_planner import build_plan_tree, plan_movie, plan_series
from services.uploads import (
    UploadError,
    append_upload_chunk,
    cancel_upload,
    create_upload_session,
    finalize_upload,
    get_upload_status,
    save_small_upload,
)

from config import (
    LOCAL_MEDIA_LIBRARIES,
    QBITTORRENT,
    QBITTORRENT_LIBRARIES,
)

app = Flask(__name__)


# ============================================================
# Background collectors
# ============================================================

start_activity_collectors()


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
        return jsonify(get_system_stats())

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


# ============================================================
# Local Media Upload
# ============================================================

@app.route("/api/media/upload/init", methods=["POST", "OPTIONS"])
def media_upload_init():
    if request.method == "OPTIONS":
        return "", 204

    try:
        result = create_upload_session(
            request.get_json(silent=True) or {}
        )
        return jsonify(result), 201

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Upload init error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się utworzyć sesji uploadu"
        }), 500


@app.route("/api/media/upload/<upload_id>", methods=["GET", "OPTIONS"])
def media_upload_status(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        return jsonify(get_upload_status(upload_id))

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Upload status error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się odczytać uploadu"
        }), 500


@app.route("/api/media/upload/<upload_id>/chunk", methods=["POST", "OPTIONS"])
def media_upload_chunk(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        result = append_upload_chunk(
            upload_id,
            request.headers.get("X-Upload-Offset", ""),
            request.stream,
            request.content_length,
        )
        return jsonify(result)

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Upload chunk error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się zapisać części pliku"
        }), 500


@app.route("/api/media/upload/<upload_id>/finalize", methods=["POST", "OPTIONS"])
def media_upload_finalize(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        return jsonify(finalize_upload(upload_id))

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Upload finalize error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się zakończyć uploadu"
        }), 500


@app.route("/api/media/upload/<upload_id>", methods=["DELETE", "OPTIONS"])
def media_upload_cancel(upload_id):
    if request.method == "OPTIONS":
        return "", 204

    try:
        return jsonify(cancel_upload(upload_id))

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Upload cancel error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się anulować uploadu"
        }), 500


@app.route("/api/media/upload", methods=["POST", "OPTIONS"])
def media_upload():
    """Small-file fallback/test uploader. Large browser uploads use sessions."""
    if request.method == "OPTIONS":
        return "", 204

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({
            "ok": False,
            "error": "Nie wybrano pliku"
        }), 400

    try:
        result = save_small_upload(
            str(request.form.get("library", "")).strip(),
            request.form.get("folder", ""),
            request.form.get("targetName"),
            upload,
        )
        return jsonify(result)

    except UploadError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Local media upload error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się przesłać pliku"
        }), 500


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