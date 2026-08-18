"""Store behaviour: cache location, collision handling, retention."""

import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pasteimg_lib import store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self._prev = os.environ.get("XDG_CACHE_HOME")
        os.environ["XDG_CACHE_HOME"] = self._tmp.name

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("XDG_CACHE_HOME", None)
        else:
            os.environ["XDG_CACHE_HOME"] = self._prev
        self._tmp.cleanup()

    def test_cache_dir_honours_xdg(self):
        self.assertEqual(store.cache_dir(), Path(self._tmp.name) / store.APP_DIR_NAME)

    def test_save_writes_bytes_and_extension(self):
        path = store.save(b"payload", "png")
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), b"payload")
        self.assertEqual(path.suffix, ".png")

    def test_same_second_saves_do_not_collide(self):
        # Both land on the same timestamp, so the second must get a suffix.
        a = store.save(b"first", "png")
        b = store.save(b"second", "png")
        self.assertNotEqual(a, b)
        self.assertEqual(a.read_bytes(), b"first")
        self.assertEqual(b.read_bytes(), b"second")

    def test_latest_returns_newest(self):
        old = store.save(b"old", "png")
        os.utime(old, (time.time() - 500, time.time() - 500))
        new = store.save(b"new", "png")
        self.assertEqual(store.latest(), new)

    def test_latest_is_none_when_empty(self):
        self.assertIsNone(store.latest())

    def test_prune_removes_only_old_files(self):
        fresh = store.save(b"fresh", "png")
        stale = store.save(b"stale", "png")
        eight_days_ago = time.time() - (8 * 86400)
        os.utime(stale, (eight_days_ago, eight_days_ago))

        removed = store.prune(days=7)

        self.assertEqual(removed, 1)
        self.assertTrue(fresh.exists())
        self.assertFalse(stale.exists())

    def test_prune_disabled_with_zero(self):
        stale = store.save(b"stale", "png")
        long_ago = time.time() - (99 * 86400)
        os.utime(stale, (long_ago, long_ago))
        self.assertEqual(store.prune(days=0), 0)
        self.assertTrue(stale.exists())

    def test_prune_ignores_foreign_files(self):
        directory = store.cache_dir()
        directory.mkdir(parents=True, exist_ok=True)
        foreign = directory / "important-notes.txt"
        foreign.write_text("not ours")
        long_ago = time.time() - (99 * 86400)
        os.utime(foreign, (long_ago, long_ago))

        store.prune(days=7)

        self.assertTrue(foreign.exists(), "prune must only touch files it created")


if __name__ == "__main__":
    unittest.main()
