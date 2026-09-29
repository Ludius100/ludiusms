[Reading 78 lines from start (total: 78 lines, 0 remaining)]

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from final_credentials import (
    FinalCredentialsError,
    collect_managed_credentials,
)


def plan(jellyfin="install", qbittorrent="install"):
    return {
        "config": {
            "services": {
                "jellyfin": jellyfin,
                "qbittorrent": qbittorrent,
                "tailscale": "install",
            }
        }
    }


class FinalCredentialsTests(unittest.TestCase):
    def test_managed_credentials_are_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secrets = root / "secrets"
            secrets.mkdir()
            (secrets / "jellyfin_admin.env").write_text(
                "JELLYFIN_ADMIN_USERNAME=lmsadmin\n"
                "JELLYFIN_ADMIN_PASSWORD=jelly-secret\n",
                encoding="utf-8",
            )
            (secrets / "qbittorrent.env").write_text(
                "QBITTORRENT_USERNAME=lmsadmin\n"
                "QBITTORRENT_PASSWORD=qb-secret\n",
                encoding="utf-8",
            )

            result = collect_managed_credentials(
                plan(),
                root,
            )
            self.assertEqual(
                result["jellyfin"]["password"],
                "jelly-secret",
            )
            self.assertEqual(
                result["qbittorrent"]["password"],
                "qb-secret",
            )

    def test_existing_services_are_never_revealed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = collect_managed_credentials(
                plan(
                    jellyfin="existing",
                    qbittorrent="existing",
                ),
                tmp,
            )
            self.assertEqual(result, {})

    def test_missing_managed_secret_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FinalCredentialsError):
                collect_managed_credentials(
                    plan(jellyfin="install", qbittorrent="skip"),
                    tmp,
                )


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]