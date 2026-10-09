from flask import Blueprint, jsonify, request

from services.qbittorrent_workflows import (
    QBitTorrentError,
    get_qbittorrent_libraries,
    get_qbittorrent_titles,
    search_qbittorrent_metadata,
    get_qbittorrent_status,
    prepare_magnet,
    start_torrent,
)


qbittorrent_bp = Blueprint(
    "qbittorrent",
    __name__,
    url_prefix="/api/qbittorrent",
)


@qbittorrent_bp.route("/libraries")
def qbittorrent_libraries():
    return jsonify({
        "libraries": get_qbittorrent_libraries()
    })


@qbittorrent_bp.route("/titles")
def qbittorrent_titles():
    try:
        return jsonify(get_qbittorrent_titles(request.args.get("library", "")))
    except QBitTorrentError as e:
        return jsonify(e.payload), e.status_code


@qbittorrent_bp.route("/metadata-search")
def qbittorrent_metadata_search():
    try:
        return jsonify(search_qbittorrent_metadata(
            request.args.get("library", ""),
            request.args.get("q", ""),
        ))
    except QBitTorrentError as e:
        return jsonify(e.payload), e.status_code


@qbittorrent_bp.route("")
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


@qbittorrent_bp.route(
    "/add",
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


@qbittorrent_bp.route(
    "/start",
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
            data.get("targetFolder"),
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

@qbittorrent_bp.route("/control", methods=["POST", "OPTIONS"])
def qbittorrent_control():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True) or {}
    try:
        from services.qbittorrent_workflows import control_torrent
        return jsonify(control_torrent(data.get("hash"), data.get("action")))
    except QBitTorrentError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("qBittorrent control error:", type(e).__name__, e, flush=True)
        return jsonify({"ok": False, "error": "Nie udało się wykonać akcji"}), 503
