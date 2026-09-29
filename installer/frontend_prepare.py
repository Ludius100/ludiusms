[Reading 163 lines from start (total: 163 lines, 0 remaining)]

#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


class FrontendPrepareError(RuntimeError):
    pass


API_LITERAL = re.compile(
    r'"http://(?:\d{1,3}\.){3}\d{1,3}:8090"'
)


def _replace_services_block(text):
    start = text.find("    const SERVICES = {")
    end_marker = "\n\n\n    function serviceCard"
    end = text.find(end_marker, start)
    if start < 0 or end < 0:
        raise FrontendPrepareError("Nie znaleziono bloku SERVICES.")

    replacement = """    const serviceUrl = (port) =>
        `${window.location.protocol}//${window.location.hostname}:${port}`;

    const SERVICES = {
        jellyfin: {
            name: "Jellyfin",
            description: "Filmy • Seriale • Anime",
            url: serviceUrl(8096),
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/jellyfin.png"
        }
    };"""

    return text[:start] + replacement + text[end:]


def _replace_static_service_info(text):
    start = text.find("    function renderStaticServiceInfo() {")
    end = text.find("\n\n\n    async function loadData()", start)
    if start < 0 or end < 0:
        raise FrontendPrepareError(
            "Nie znaleziono renderStaticServiceInfo()."
        )
    replacement = """    function renderStaticServiceInfo() {
        // Optional personal services are intentionally omitted in distribution builds.
    }"""
    return text[:start] + replacement + text[end:]


def prepare_custom_js(source):
    text = source

    text = API_LITERAL.sub('""', text)
    text = re.sub(
        r'    const WALLPAPER_API = "http://(?:\d{1,3}\.){3}\d{1,3}:8088";',
        "    const WALLPAPER_API = null;",
        text,
        count=1,
    )
    text = _replace_services_block(text)
    text = _replace_static_service_info(text)

    for service_id in ("gdrive", "kuma", "ntfy"):
        text = text.replace(
            f'                            ${{serviceCard("{service_id}")}}\n',
            "",
        )

    text = re.sub(
        r"<strong>[^<]+</strong>\s*\n\s*</div>\s*\n\s*\n\s*<div class=\"nas-global-status\">",
        "<strong>LMS</strong>\n                            </div>\n\n"
        "                            <div class=\"nas-global-status\">",
        text,
        count=1,
    )
    text = text.replace(
        "                        NAS • Oracle Cloud",
        "                        LMS Server",
        1,
    )

    marker = "    function renderStatus(status) {\n        let onlineCount = 0;"
    if marker not in text:
        raise FrontendPrepareError("Nie znaleziono renderStatus().")
    text = text.replace(
        marker,
        marker + "\n        const totalServices = Object.keys(SERVICES).length;",
        1,
    )
    text = text.replace(
        "`${onlineCount} / 4 online`",
        "`${onlineCount} / ${totalServices} online`",
        1,
    )
    text = text.replace("onlineCount === 4", "onlineCount === totalServices", 1)
    text = text.replace(
        "`${onlineCount} z 4 usług online`",
        "`${onlineCount} z ${totalServices} usług online`",
        1,
    )

    apply_marker = "    function applyWallpaper() {\n"
    if apply_marker not in text:
        raise FrontendPrepareError("Nie znaleziono applyWallpaper().")
    text = text.replace(
        apply_marker,
        apply_marker + "        if (!WALLPAPER_API) return;\n",
        1,
    )

    actions_marker = """        const wallpaperInput =
            document.getElementById(
                "wallpaper-input"
            );


        refreshButton.addEventListener("""
    if actions_marker not in text:
        raise FrontendPrepareError("Nie znaleziono setupActions().")
    text = text.replace(
        actions_marker,
        """        const wallpaperInput =
            document.getElementById(
                "wallpaper-input"
            );

        if (!WALLPAPER_API) {
            wallpaperButton?.remove();
            wallpaperInput?.remove();
            refreshButton.addEventListener("click", loadData);
            return;
        }


        refreshButton.addEventListener(""",
        1,
    )

    return text


def main():
    parser = argparse.ArgumentParser(
        description="Prepare a portable LMS Homepage custom.js"
    )
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8")
    prepared = prepare_custom_js(source)

    destination = Path(args.destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(prepared, encoding="utf-8")

    print(f"prepared: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]