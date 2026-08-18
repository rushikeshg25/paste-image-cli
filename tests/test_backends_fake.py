"""Core flow driven against an in-memory backend.

This is the payoff of the Clipboard seam: the whole flow, including the
file-reuse branch, is testable on any OS with no real clipboard involved.
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pasteimg_lib import core, store
from pasteimg_lib.backends.base import Clipboard


class FakeClipboard(Clipboard):
    name = "fake"

    def __init__(self, image=None, file_urls=None):
        self._image = image
        self._file_urls = file_urls or []
        self.written_text = None
        self.notifications = []

    @classmethod
    def available(cls):
        return True

    def read_image(self):
        return self._image

    def read_file_urls(self):
        return self._file_urls

    def write_text(self, text):
        self.written_text = text

    def notify(self, title, body):
        self.notifications.append((title, body))


class CoreFlowTest(unittest.TestCase):
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

    def test_saves_raw_image_to_cache(self):
        cb = FakeClipboard(image=(b"\x89PNG-data", "png"))

        result = core.grab(cb)

        self.assertFalse(result.reused)
        self.assertEqual(result.backend, "fake")
        self.assertEqual(result.size, len(b"\x89PNG-data"))
        self.assertEqual(result.path.read_bytes(), b"\x89PNG-data")
        self.assertEqual(result.path.parent, store.cache_dir())

    def test_reuses_existing_file_without_copying(self):
        existing = Path(self._tmp.name) / "screenshot.png"
        existing.write_bytes(b"already-on-disk")
        cb = FakeClipboard(file_urls=[str(existing)])

        result = core.grab(cb)

        self.assertTrue(result.reused)
        self.assertEqual(result.path, existing)
        self.assertFalse(store.cache_dir().exists(), "must not duplicate a file that is already on disk")

    def test_file_url_wins_over_raw_image(self):
        existing = Path(self._tmp.name) / "shot.png"
        existing.write_bytes(b"on-disk")
        cb = FakeClipboard(image=(b"raw", "png"), file_urls=[str(existing)])

        self.assertTrue(core.grab(cb).reused)

    def test_missing_file_url_falls_back_to_raw_image(self):
        cb = FakeClipboard(image=(b"raw", "png"), file_urls=["/nonexistent/gone.png"])

        result = core.grab(cb)

        self.assertFalse(result.reused)
        self.assertEqual(result.path.read_bytes(), b"raw")

    def test_no_image_raises(self):
        with self.assertRaises(core.NoImageError):
            core.grab(FakeClipboard())

    def test_extension_follows_image_type(self):
        result = core.grab(FakeClipboard(image=(b"jpeg-bytes", "jpg")))
        self.assertEqual(result.path.suffix, ".jpg")

    def test_as_dict_shape(self):
        result = core.grab(FakeClipboard(image=(b"x", "png")))
        self.assertEqual(
            set(result.as_dict()), {"path", "bytes", "backend", "reused"}
        )


class BackendDetectionTest(unittest.TestCase):
    def test_probe_order_prefers_wayland_over_x11(self):
        from pasteimg_lib.backends import _PROBE
        from pasteimg_lib.backends.wayland import WaylandClipboard
        from pasteimg_lib.backends.x11 import X11Clipboard

        self.assertLess(_PROBE.index(WaylandClipboard), _PROBE.index(X11Clipboard))

    def test_every_backend_implements_the_interface(self):
        from pasteimg_lib.backends import _PROBE

        for cls in _PROBE:
            with self.subTest(backend=cls.__name__):
                self.assertFalse(getattr(cls, "__abstractmethods__", None))
                self.assertNotEqual(cls.name, "unknown")


if __name__ == "__main__":
    unittest.main()
