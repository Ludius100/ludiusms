import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from host_ops import HostOps


class SecretBindMountTests(unittest.TestCase):
    def test_mounted_secret_update_preserves_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'jellyfin_api_key'
            path.write_text('', encoding='utf-8')
            inode_before = path.stat().st_ino
            runner = HostOps(enabled=True)
            runner.write_text(path, 'new-token\n', action_id='jellyfin.bootstrap', mode=0o600, preserve_inode=True)
            self.assertEqual(path.stat().st_ino, inode_before)
            self.assertEqual(path.read_text(encoding='utf-8'), 'new-token\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_other_writes_remain_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'regular-config'
            path.write_text('old', encoding='utf-8')
            inode_before = path.stat().st_ino
            runner = HostOps(enabled=True)
            runner.write_text(path, 'new', action_id='config')
            self.assertNotEqual(path.stat().st_ino, inode_before)
            self.assertEqual(path.read_text(encoding='utf-8'), 'new')


if __name__ == '__main__':
    unittest.main()
