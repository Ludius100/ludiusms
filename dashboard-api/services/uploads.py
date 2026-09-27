import json
import os
import time
import uuid

from config import (
    LOCAL_MEDIA_LIBRARIES,
    UPLOAD_CHUNK_MAX,
    UPLOAD_STAGING_DIR,
    UPLOAD_STATE_DIR,
)
from services.media_paths import path_is_inside, safe_media_component


_NAS_UID = 1002
_NAS_GID = 1003
_DIRECTORY_MODE = 0o2770
_FILE_MODE = 0o660
_STREAM_BLOCK_SIZE = 1024 * 1024


class UploadError(Exception):
    def __init__(self, message, status_code=400, **details):
        super().__init__(message)
        self.status_code = status_code
        self.payload = {
            "ok": False,
            "error": message,
            **details,
        }


def _set_nas_permissions(path):
    os.chown(path, _NAS_UID, _NAS_GID)

    if os.path.isdir(path):
        os.chmod(path, _DIRECTORY_MODE)
    else:
        os.chmod(path, _FILE_MODE)


def _upload_state_path(upload_id):
    upload_id = str(upload_id or "").strip().lower()

    if (
        len(upload_id) != 32
        or any(c not in "0123456789abcdef" for c in upload_id)
    ):
        raise UploadError(
            "Nie znaleziono sesji uploadu",
            404,
        )

    return os.path.join(
        UPLOAD_STATE_DIR,
        upload_id + ".json",
    )


def _load_upload_state(upload_id):
    path = _upload_state_path(upload_id)

    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (FileNotFoundError, ValueError):
        raise UploadError(
            "Nie znaleziono sesji uploadu",
            404,
        )

    if not isinstance(state, dict):
        raise UploadError(
            "Nie znaleziono sesji uploadu",
            404,
        )

    return state


def _save_upload_state(state):
    os.makedirs(UPLOAD_STATE_DIR, exist_ok=True)
    path = _upload_state_path(state["id"])
    temporary = path + ".tmp"

    try:
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2,
            )

        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            try:
                os.remove(temporary)
            except OSError:
                pass


def _delete_upload_state(upload_id):
    try:
        os.remove(_upload_state_path(upload_id))
    except FileNotFoundError:
        pass


def _public_upload_state(state):
    staging_path = state["stagingPath"]
    received = (
        os.path.getsize(staging_path)
        if os.path.exists(staging_path)
        else 0
    )
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
        "chunkMax": UPLOAD_CHUNK_MAX,
    }


def _prepare_upload_target(data):
    library_id = str(
        data.get("library", "")
    ).strip()
    library = LOCAL_MEDIA_LIBRARIES.get(library_id)

    if not library:
        raise UploadError(
            "Nieprawidłowa biblioteka lokalnych mediów",
            400,
        )

    raw_folder = str(
        data.get("folder", "") or ""
    ).replace("\\", "/").strip("/")

    folder_parts = []
    for part in raw_folder.split("/"):
        if not part or part in (".", ".."):
            continue
        folder_parts.append(
            safe_media_component(part, "media")
        )

    if not folder_parts:
        folder_parts = ["Nowe media"]

    folder_name = "/".join(folder_parts)
    original_name = safe_media_component(
        data.get("originalName", ""),
        "media.bin",
    )
    target_name = safe_media_component(
        data.get("targetName") or original_name,
        original_name,
    )

    try:
        size = int(data.get("size"))
    except (TypeError, ValueError):
        raise UploadError(
            "Nieprawidłowy rozmiar pliku",
            400,
        )

    if size < 0:
        raise UploadError(
            "Nieprawidłowy rozmiar pliku",
            400,
        )

    library_root = os.path.realpath(
        library["path"]
    )
    destination_dir = os.path.join(
        library_root,
        *folder_parts,
    )
    destination = os.path.join(
        destination_dir,
        target_name,
    )

    if not path_is_inside(
        destination_dir,
        library_root,
    ):
        raise UploadError(
            "Nieprawidłowa ścieżka docelowa",
            400,
        )

    if not path_is_inside(
        destination,
        library_root,
    ):
        raise UploadError(
            "Nieprawidłowa nazwa pliku",
            400,
        )

    return (
        library_id,
        library,
        folder_name,
        original_name,
        target_name,
        size,
        destination_dir,
        destination,
    )


def create_upload_session(data):
    (
        library_id,
        library,
        folder_name,
        original_name,
        target_name,
        size,
        destination_dir,
        destination,
    ) = _prepare_upload_target(data)

    if os.path.exists(destination):
        raise UploadError(
            "Plik docelowy już istnieje",
            409,
            conflict=True,
            target=destination,
        )

    os.makedirs(
        UPLOAD_STAGING_DIR,
        exist_ok=True,
    )
    _set_nas_permissions(UPLOAD_STAGING_DIR)

    upload_id = uuid.uuid4().hex
    staging_path = os.path.join(
        UPLOAD_STAGING_DIR,
        upload_id + ".part",
    )

    try:
        with open(staging_path, "xb"):
            pass
        _set_nas_permissions(staging_path)

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
            "createdAt": int(time.time()),
        }
        _save_upload_state(state)
    except Exception:
        try:
            if os.path.exists(staging_path):
                os.remove(staging_path)
        finally:
            raise

    return _public_upload_state(state)


def get_upload_status(upload_id):
    state = _load_upload_state(upload_id)
    return _public_upload_state(state)


def append_upload_chunk(
    upload_id,
    offset_value,
    stream,
    content_length,
):
    state = _load_upload_state(upload_id)
    staging_path = state["stagingPath"]
    expected_size = int(state["size"])

    if not os.path.exists(staging_path):
        raise UploadError(
            "Nie znaleziono sesji uploadu",
            404,
        )

    try:
        offset = int(offset_value)
    except (TypeError, ValueError):
        raise UploadError(
            "Brak lub błędny X-Upload-Offset",
            400,
        )

    current_size = os.path.getsize(staging_path)

    if offset != current_size:
        raise UploadError(
            "Offset nie zgadza się ze stanem serwera",
            409,
            expectedOffset=current_size,
        )

    if (
        content_length is not None
        and content_length > UPLOAD_CHUNK_MAX
    ):
        raise UploadError(
            "Chunk jest zbyt duży",
            413,
            chunkMax=UPLOAD_CHUNK_MAX,
        )

    remaining = expected_size - current_size
    if remaining <= 0:
        return _public_upload_state(state)

    written = 0

    try:
        with open(staging_path, "ab") as f:
            while True:
                read_limit = min(
                    _STREAM_BLOCK_SIZE,
                    UPLOAD_CHUNK_MAX - written + 1,
                )
                block = stream.read(read_limit)

                if not block:
                    break

                written += len(block)

                if (
                    written > UPLOAD_CHUNK_MAX
                    or written > remaining
                ):
                    raise UploadError(
                        "Chunk przekracza dozwolony rozmiar uploadu",
                        413,
                    )

                f.write(block)

            f.flush()
            os.fsync(f.fileno())

    except Exception:
        try:
            with open(staging_path, "r+b") as f:
                f.truncate(current_size)
        except OSError:
            pass
        raise

    _set_nas_permissions(staging_path)

    result = _public_upload_state(state)
    result["written"] = written
    return result


def finalize_upload(upload_id):
    state = _load_upload_state(upload_id)
    staging_path = state["stagingPath"]
    destination_dir = state["destinationDir"]
    destination = state["destination"]
    expected_size = int(state["size"])

    if not os.path.exists(staging_path):
        raise UploadError(
            "Brak pliku tymczasowego",
            409,
        )

    received = os.path.getsize(staging_path)

    if received != expected_size:
        raise UploadError(
            "Upload nie jest kompletny",
            409,
            received=received,
            size=expected_size,
        )

    if os.path.exists(destination):
        raise UploadError(
            "Plik docelowy już istnieje",
            409,
            conflict=True,
            target=destination,
        )

    os.makedirs(
        destination_dir,
        exist_ok=True,
    )
    _set_nas_permissions(destination_dir)

    if os.path.exists(destination):
        raise UploadError(
            "Plik docelowy pojawił się podczas uploadu",
            409,
            conflict=True,
            target=destination,
        )

    os.replace(staging_path, destination)
    _set_nas_permissions(destination)
    _delete_upload_state(upload_id)

    return {
        "ok": True,
        "uploadId": upload_id,
        "library": state["library"],
        "libraryName": state["libraryName"],
        "folder": state["folder"],
        "originalName": state["originalName"],
        "name": state["name"],
        "path": destination,
        "size": os.path.getsize(destination),
    }


def cancel_upload(upload_id):
    state = _load_upload_state(upload_id)
    staging_path = state["stagingPath"]

    if os.path.exists(staging_path):
        os.remove(staging_path)

    _delete_upload_state(upload_id)

    return {
        "ok": True,
        "cancelled": True,
        "uploadId": upload_id,
    }


def save_small_upload(
    library_id,
    folder_value,
    target_value,
    upload,
):
    library = LOCAL_MEDIA_LIBRARIES.get(
        library_id
    )

    if not library:
        raise UploadError(
            "Nieprawidłowa biblioteka lokalnych mediów",
            400,
        )

    folder_name = safe_media_component(
        folder_value,
        "Nowe media",
    )
    original_name = safe_media_component(
        os.path.basename(
            str(upload.filename).replace("\\", "/")
        ),
        "media.bin",
    )
    target_name = safe_media_component(
        target_value or original_name,
        original_name,
    )

    library_root = os.path.realpath(
        library["path"]
    )
    destination_dir = os.path.join(
        library_root,
        folder_name,
    )
    destination = os.path.join(
        destination_dir,
        target_name,
    )

    if (
        not path_is_inside(
            destination_dir,
            library_root,
        )
        or not path_is_inside(
            destination,
            library_root,
        )
    ):
        raise UploadError(
            "Nieprawidłowa ścieżka docelowa",
            400,
        )

    if os.path.exists(destination):
        raise UploadError(
            "Plik docelowy już istnieje",
            409,
            conflict=True,
            target=destination,
        )

    os.makedirs(
        destination_dir,
        exist_ok=True,
    )
    _set_nas_permissions(destination_dir)

    temporary_path = os.path.join(
        destination_dir,
        ".upload-" + uuid.uuid4().hex + ".part",
    )

    try:
        upload.save(temporary_path)
        _set_nas_permissions(temporary_path)

        if os.path.exists(destination):
            raise UploadError(
                "Plik docelowy pojawił się podczas uploadu",
                409,
                conflict=True,
                target=destination,
            )

        os.replace(
            temporary_path,
            destination,
        )
        temporary_path = None
        _set_nas_permissions(destination)

    finally:
        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            try:
                os.remove(temporary_path)
            except OSError:
                pass

    return {
        "ok": True,
        "library": library_id,
        "libraryName": library["name"],
        "folder": folder_name,
        "originalName": original_name,
        "name": target_name,
        "path": destination,
        "size": os.path.getsize(destination),
    }
