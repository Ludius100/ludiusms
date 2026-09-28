from flask import Blueprint, jsonify, request

from modules.registry import get_module_manifest
from services.activity import load_activity
from services.system import get_service_statuses, get_system_stats


core_bp = Blueprint(
    "core",
    __name__,
    url_prefix="/api",
)


@core_bp.route("/activity")
def activity():
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20

    limit = max(1, min(limit, 100))

    return jsonify({
        "events": load_activity()[:limit]
    })


@core_bp.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@core_bp.route("/modules")
def modules():
    return jsonify(get_module_manifest())


@core_bp.route("/system")
def system_stats():
    try:
        return jsonify(get_system_stats())

    except Exception as e:
        print("System API error:", e)

        return jsonify({
            "error": "System stats unavailable"
        }), 503


@core_bp.route("/status")
def status():
    return jsonify(get_service_statuses())
