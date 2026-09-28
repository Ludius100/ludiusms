import os

from config import (
    NAS_DIRECTORY_MODE,
    NAS_FILE_MODE,
    NAS_GID,
    NAS_UID,
)


def set_nas_permissions(path):
    os.chown(path, NAS_UID, NAS_GID)

    mode = (
        NAS_DIRECTORY_MODE
        if os.path.isdir(path)
        else NAS_FILE_MODE
    )
    os.chmod(path, mode)


def ensure_nas_directory(path):
    os.makedirs(path, exist_ok=True)
    set_nas_permissions(path)
    return path
