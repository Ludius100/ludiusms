from flask import Blueprint, jsonify, request

from services.qbittorrent_workflows import (
    QBitTorrentError,
    get_qbittorrent_libraries,
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
