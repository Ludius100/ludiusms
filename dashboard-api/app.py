from flask import Flask, jsonify, request
import os

from services.jellyfin import jellyfin_get

from services.qbittorrent_workflows import (
    QBitTorrentError,
    get_qbittorrent_libraries,
    get_qbittorrent_status,
    prepare_magnet,
    start_torrent,
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
        "libraries": get_qbittorrent_libraries()
    })


@app.route("/api/qbittorrent")
def qbittorrent_status():
    try:
        return jsonify(get_qbittorrent_status())

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

    data = request.get_json(silent=True) or {}

    try:
        result = prepare_magnet(
            data.get("magnet"),
            data.get("library", "downloads"),
        )
        return jsonify(result)

    except QBitTorrentError as e:
        return jsonify(e.payload), e.status_code
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

    data = request.get_json(silent=True) or {}

    try:
        result = start_torrent(
            data.get("hash"),
            data.get("selected", []),
        )
        return jsonify(result)

    except QBitTorrentError as e:
        return jsonify(e.payload), e.status_code
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