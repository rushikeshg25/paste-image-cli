"""Wayland backend process behaviour."""

import unittest
from unittest.mock import patch

from pasteimg_lib.backends.wayland import WaylandClipboard


class WaylandClipboardTest(unittest.TestCase):
    @patch.object(WaylandClipboard, "_run")
    def test_write_text_does_not_capture_forked_wl_copy_output(self, run):
        WaylandClipboard().write_text("/tmp/clip.png")

        run.assert_called_once_with(
            ["wl-copy", "--type", "text/plain"],
            stdin=b"/tmp/clip.png",
            capture_output=False,
        )


if __name__ == "__main__":
    unittest.main()
