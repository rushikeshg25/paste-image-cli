"""Wayland backend process behaviour."""

import subprocess
import unittest
from unittest.mock import patch

from pasteimg_lib.backends.base import BackendError
from pasteimg_lib.backends.wayland import WaylandClipboard


class WaylandClipboardTest(unittest.TestCase):
    @patch("pasteimg_lib.backends.wayland.subprocess.run")
    def test_write_text_does_not_capture_forked_wl_copy_output(self, run):
        run.return_value = subprocess.CompletedProcess([], 0)

        WaylandClipboard().write_text("/tmp/clip.png")

        run.assert_called_once_with(
            ["wl-copy", "--type", "text/plain"],
            input=b"/tmp/clip.png",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    @patch("pasteimg_lib.backends.wayland.subprocess.run")
    def test_write_text_wraps_nonzero_exit(self, run):
        run.return_value = subprocess.CompletedProcess([], 7)

        with self.assertRaisesRegex(BackendError, r"wl-copy failed: exit 7"):
            WaylandClipboard().write_text("/tmp/clip.png")

    @patch("pasteimg_lib.backends.wayland.subprocess.run", side_effect=FileNotFoundError)
    def test_write_text_wraps_missing_command(self, run):
        with self.assertRaisesRegex(BackendError, r"wl-copy not found"):
            WaylandClipboard().write_text("/tmp/clip.png")


if __name__ == "__main__":
    unittest.main()
