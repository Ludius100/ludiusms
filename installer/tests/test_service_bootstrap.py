[Reading 221 lines from start (total: 221 lines, 0 remaining)]

import json
import sys
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from service_bootstrap import (
    extract_qbittorrent_temp_password,
    jellyfin_add_library,
    jellyfin_authenticate,
    jellyfin_bootstrap,
    jellyfin_get_libraries,
    qbittorrent_bootstrap,
)


class FakeServicesHandler(BaseHTTPRequestHandler):
    state = {
        "qb_user": "admin",
        "qb_password": "TEMP1234",
        "jellyfin_user": None,
        "jellyfin_password": None,
        "libraries": [],
    }

    def log_message(self, *args):
        pass
    def _body(self):
        size = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(size) if size else b""

    def _reply(self, status=200, body=b"", headers=None):
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/System/Info/Public":
            return self._reply(200, b"{}")
        if self.path == "/Library/VirtualFolders":
            payload = json.dumps(self.state["libraries"]).encode()
            return self._reply(
                200,
                payload,
                {"Content-Type": "application/json"},
            )
        return self._reply(404)

    def do_POST(self):
        body = self._body()

        if self.path == "/api/v2/auth/login":
            data = urllib.parse.parse_qs(body.decode())
            user = data.get("username", [""])[0]
            password = data.get("password", [""])[0]
            if (
                user == self.state["qb_user"]
                and password == self.state["qb_password"]
            ):
                return self._reply(
                    200,
                    b"Ok.",
                    {"Set-Cookie": "SID=fake; path=/"},
                )
            return self._reply(200, b"Fails.")
        if self.path == "/api/v2/app/setPreferences":
            data = urllib.parse.parse_qs(body.decode())
            prefs = json.loads(data["json"][0])
            self.state["qb_user"] = prefs["web_ui_username"]
            self.state["qb_password"] = prefs["web_ui_password"]
            self.state["qb_save_path"] = prefs["save_path"]
            return self._reply(200)

        if self.path == "/Startup/Configuration":
            self.state["startup_configuration"] = json.loads(body)
            return self._reply(204)

        if self.path == "/Startup/User":
            payload = json.loads(body)
            self.state["jellyfin_user"] = payload["Name"]
            self.state["jellyfin_password"] = payload["Password"]
            return self._reply(204)

        if self.path == "/Startup/RemoteAccess":
            self.state["remote_access"] = json.loads(body)
            return self._reply(204)

        if self.path == "/Startup/Complete":
            self.state["startup_complete"] = True
            return self._reply(204)

        if self.path == "/Users/AuthenticateByName":
            payload = json.loads(body)
            if (
                payload["Username"] == self.state["jellyfin_user"]
                and payload["Pw"] == self.state["jellyfin_password"]
            ):
                return self._reply(
                    200,
                    json.dumps({"AccessToken": "JF-TOKEN"}).encode(),
                    {"Content-Type": "application/json"},
                )
            return self._reply(401)
        if self.path.startswith("/Library/VirtualFolders?"):
            query = urllib.parse.parse_qs(
                urllib.parse.urlsplit(self.path).query
            )
            self.state["libraries"].append({
                "Name": query["name"][0],
                "CollectionType": query["collectionType"][0],
                "Locations": query.get("paths", []),
            })
            return self._reply(204)

        return self._reply(404)


class ServiceBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            FakeServicesHandler,
        )
        cls.thread = threading.Thread(
            target=cls.server.serve_forever,
            daemon=True,
        )
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeServicesHandler.state.update({
            "qb_user": "admin",
            "qb_password": "TEMP1234",
            "libraries": [],
        })
    def test_extract_qbittorrent_temp_password(self):
        logs = (
            "WebUI administrator password was not set. "
            "A temporary password is provided for this session: AbC123xyz"
        )
        self.assertEqual(
            extract_qbittorrent_temp_password(logs),
            "AbC123xyz",
        )

    def test_qbittorrent_bootstrap_changes_credentials(self):
        self.assertTrue(
            qbittorrent_bootstrap(
                self.base,
                temporary_password="TEMP1234",
                username="lmsadmin",
                password="FINAL-PASSWORD",
            )
        )
        self.assertEqual(
            FakeServicesHandler.state["qb_user"],
            "lmsadmin",
        )
        self.assertEqual(
            FakeServicesHandler.state["qb_save_path"],
            "/nas/Downloads",
        )

    def test_jellyfin_bootstrap_returns_access_token(self):
        token = jellyfin_bootstrap(
            self.base,
            username="lmsadmin",
            password="JF-PASSWORD",
        )
        self.assertEqual(token, "JF-TOKEN")
        self.assertTrue(
            FakeServicesHandler.state["startup_complete"]
        )
        self.assertEqual(
            FakeServicesHandler.state["startup_configuration"][
                "MetadataCountryCode"
            ],
            "PL",
        )
    def test_jellyfin_library_creation(self):
        FakeServicesHandler.state["jellyfin_user"] = "lmsadmin"
        FakeServicesHandler.state["jellyfin_password"] = "JF-PASSWORD"
        token = jellyfin_authenticate(
            self.base,
            username="lmsadmin",
            password="JF-PASSWORD",
        )
        jellyfin_add_library(
            self.base,
            token,
            name="Anime",
            collection_type="tvshows",
            paths=["/media/Anime/Seriale"],
        )
        libraries = jellyfin_get_libraries(self.base, token)

        self.assertEqual(len(libraries), 1)
        self.assertEqual(libraries[0]["Name"], "Anime")
        self.assertEqual(
            libraries[0]["CollectionType"],
            "tvshows",
        )


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]