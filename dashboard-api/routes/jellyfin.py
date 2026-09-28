from flask import Blueprint, jsonify

from services.jellyfin import get_jellyfin_summary


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

        return jsonify({
            "online": False
        }), 503
