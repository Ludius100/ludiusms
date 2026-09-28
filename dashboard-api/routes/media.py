from flask import Blueprint, jsonify, request

from services.media_library import (
    MediaLibraryError,
    get_last_episode,
    get_media_titles,
)
from services.media_planner import (
    MediaPlannerError,
    create_media_plan,
)
from services.uploads import (
    UploadError,
    append_upload_chunk,
    cancel_upload,
    create_upload_session,
    finalize_upload,
    get_upload_status,
    save_small_upload,
)


media_bp = Blueprint(
    "media",
    __name__,
    url_prefix="/api/media",
)


@media_bp.route("/titles", methods=["GET", "OPTIONS"])
def media_titles():
    if request.method == "OPTIONS":
        return "", 204

    try:
        return jsonify(get_media_titles(request.args.get("library", "")))

    except MediaLibraryError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Media titles error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się odczytać listy tytułów"
        }), 500


@media_bp.route("/last-episode", methods=["GET", "OPTIONS"])
def media_last_episode():
    if request.method == "OPTIONS":
        return "", 204

    try:
        result = get_last_episode(
            request.args.get("library", ""),
            request.args.get("title", ""),
            request.args.get("season", 1),
        )
        return jsonify(result)

    except MediaLibraryError as e:
        return jsonify(e.payload), e.status_code
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


@media_bp.route("/plan", methods=["POST", "OPTIONS"])
def media_plan():
    if request.method == "OPTIONS":
        return "", 204

    try:
        result = create_media_plan(
            request.get_json(silent=True) or {}
        )
        return jsonify(result)

    except MediaPlannerError as e:
        return jsonify(e.payload), e.status_code
    except Exception as e:
        print("Media planner error:", type(e).__name__, e, flush=True)
        return jsonify({
            "ok": False,
            "error": "Nie udało się przygotować planu mediów"
        }), 500


# ============================================================
# Local Media Upload
# ============================================================

@media_bp.route("/upload/init", methods=["POST", "OPTIONS"])
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


@media_bp.route("/upload/<upload_id>", methods=["GET", "OPTIONS"])
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


@media_bp.route("/upload/<upload_id>/chunk", methods=["POST", "OPTIONS"])
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


@media_bp.route("/upload/<upload_id>/finalize", methods=["POST", "OPTIONS"])
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


@media_bp.route("/upload/<upload_id>", methods=["DELETE", "OPTIONS"])
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


@media_bp.route("/upload", methods=["POST", "OPTIONS"])
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
