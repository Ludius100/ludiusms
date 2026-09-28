from importlib import import_module

from config import ENABLE_JELLYFIN, ENABLE_QBITTORRENT


MODULES = {
    "jellyfin": {
        "name": "Jellyfin",
        "enabled": ENABLE_JELLYFIN,
        "apiPrefix": "/api/jellyfin",
        "blueprint": "routes.jellyfin:jellyfin_bp",
        "collector": (
            "services.jellyfin_activity:"
            "start_activity_collectors"
        ),
    },
    "qbittorrent": {
        "name": "qBittorrent",
        "enabled": ENABLE_QBITTORRENT,
        "apiPrefix": "/api/qbittorrent",
        "blueprint": (
            "routes.qbittorrent:qbittorrent_bp"
        ),
        "collector": None,
    },
}


def load_component(reference):
    module_name, attribute = reference.split(":", 1)
    module = import_module(module_name)
    return getattr(module, attribute)


def iter_enabled_modules():
    for module_id, module in MODULES.items():
        if module["enabled"]:
            yield module_id, module


def get_module_manifest():
    return {
        "modules": {
            module_id: {
                "name": module["name"],
                "enabled": module["enabled"],
                "apiPrefix": module["apiPrefix"],
            }
            for module_id, module in MODULES.items()
        }
    }
