[Reading 98 lines from start (total: 98 lines, 0 remaining)]

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from interaction_inputs import (
    InteractionInputError,
    save_existing_jellyfin_credentials,
    save_existing_qbittorrent_credentials,
)


class InteractionInputTests(unittest.TestCase):
    def test_qbittorrent_credentials_are_validated_and_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / "secrets" / "qbittorrent.env"
            with patch(
                "interaction_inputs.qbittorrent_login_ok",
                return_value=True,
            ) as login_ok:
                save_existing_qbittorrent_credentials(
                    base_url="http://127.0.0.1:8080",
                    username="admin",
                    password="secret-pass",
                    secret_path=secret,
                )

            login_ok.assert_called_once_with(
                "http://127.0.0.1:8080",
                "admin",
                "secret-pass",
            )
            text = secret.read_text(encoding="utf-8")
            self.assertIn("QBITTORRENT_USERNAME=admin", text)
            self.assertIn("QBITTORRENT_PASSWORD=secret-pass", text)
            self.assertEqual(
                stat.S_IMODE(secret.stat().st_mode),
                0o600,
            )

    def test_invalid_qbittorrent_credentials_are_not_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / "secrets" / "qbittorrent.env"
            with patch(
                "interaction_inputs.qbittorrent_login_ok",
                return_value=False,
            ):
                with self.assertRaises(InteractionInputError):
                    save_existing_qbittorrent_credentials(
                        base_url="http://127.0.0.1:8080",
                        username="admin",
                        password="bad",
                        secret_path=secret,
                    )
            self.assertFalse(secret.exists())

    def test_jellyfin_password_is_not_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            token_file = Path(tmp) / "secrets" / "jellyfin_api_key"
            with patch(
                "interaction_inputs.jellyfin_authenticate",
                return_value="token-123",
            ):
                save_existing_jellyfin_credentials(
                    base_url="http://127.0.0.1:8096",
                    username="admin",
                    password="super-secret-password",
                    token_path=token_file,
                )

            text = token_file.read_text(encoding="utf-8")
            self.assertEqual(text, "token-123\n")
            self.assertNotIn("super-secret-password", text)
            self.assertEqual(
                stat.S_IMODE(token_file.stat().st_mode),
                0o600,
            )

    def test_newlines_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / "qbittorrent.env"
            with self.assertRaises(InteractionInputError):
                save_existing_qbittorrent_credentials(
                    base_url="http://127.0.0.1:8080",
                    username="admin",
                    password="bad\nvalue",
                    secret_path=secret,
                )


if __name__ == "__main__":
    unittest.main()

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]