import re

from flask import Blueprint, Response, jsonify, request

from services.jellyfin import (
    get_jellyfin_recent,
    get_jellyfin_summary,
    jellyfin_raw,
)


jellyfin_bp = Blueprint(
    "jellyfin",
    __name__,
    url_prefix="/api/jellyfin",
)


@jellyfin_bp.route("")
def jellyfin():
    try:
        return jsonify(get_jellyfin_summary())
    except Exception as e:
        print("Jellyfin API error:", e)
        return jsonify({"online": False}), 503


@jellyfin_bp.route("/recent")
def jellyfin_recent():
    try:
        limit = request.args.get("limit", default=8, type=int)
        return jsonify(get_jellyfin_recent(limit=limit))
    except Exception as e:
        print("Jellyfin recent API error:", e)
        return jsonify({"items": []}), 503


@jellyfin_bp.route("/image/<item_id>")
def jellyfin_image(item_id):
    if not re.fullmatch(r"[A-Za-z0-9-]{8,80}", item_id or ""):
        return jsonify({"error": "invalid_item_id"}), 400
    try:
        data, content_type = jellyfin_raw(
            f"/Items/{item_id}/Images/Primary?maxHeight=520&quality=84"
        )
        return Response(data, mimetype=content_type or "image/jpeg")
    except Exception as e:
        print("Jellyfin image API error:", e)
        return jsonify({"error": "image_unavailable"}), 404
