"""macOS backend behavior without touching the real clipboard."""

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pasteimg_lib.backends.macos import MacOSClipboard


class MacOSClipboardTest(unittest.TestCase):
    @patch.object(MacOSClipboard, "_run")
    def test_write_text_uses_pbcopy(self, run):
        MacOSClipboard().write_text("/tmp/clip.png")

        run.assert_called_once_with(["pbcopy"], stdin=b"/tmp/clip.png")

    def test_no_image_returns_none_without_extracting(self):
        clipboard = MacOSClipboard()
        with (
            patch.object(clipboard, "_clipboard_info", return_value="string"),
            patch.object(clipboard, "_extract") as extract,
        ):
            self.assertIsNone(clipboard.read_image())
            extract.assert_not_called()

    def test_reads_png_without_conversion(self):
        clipboard = MacOSClipboard()
        with (
            patch.object(clipboard, "_clipboard_info", return_value="PNGf"),
            patch.object(clipboard, "_extract", return_value=b"png-data") as extract,
            patch.object(clipboard, "_tiff_to_png") as convert,
        ):
            self.assertEqual(clipboard.read_image(), (b"png-data", "png"))
            extract.assert_called_once_with("PNGf")
            convert.assert_not_called()

    def test_converts_tiff_to_png(self):
        clipboard = MacOSClipboard()
        with (
            patch.object(clipboard, "_clipboard_info", return_value="TIFF"),
            patch.object(clipboard, "_extract", return_value=b"tiff-data"),
            patch.object(clipboard, "_tiff_to_png", return_value=b"png-data"),
        ):
            self.assertEqual(clipboard.read_image(), (b"png-data", "png"))

    def test_keeps_tiff_when_conversion_fails(self):
        clipboard = MacOSClipboard()
        with (
            patch.object(clipboard, "_clipboard_info", return_value="TIFF"),
            patch.object(clipboard, "_extract", return_value=b"tiff-data"),
            patch.object(clipboard, "_tiff_to_png", return_value=None),
        ):
            self.assertEqual(clipboard.read_image(), (b"tiff-data", "tiff"))

    @patch.object(MacOSClipboard, "_run")
    def test_reads_existing_image_file_url(self, run):
        clipboard = MacOSClipboard()
        with TemporaryDirectory() as tmp:
            image = Path(tmp) / "screen shot.png"
            image.write_bytes(b"png-data")
            run.return_value = subprocess.CompletedProcess(
                ["osascript"], 0, stdout=(image.as_uri() + "\n").encode(), stderr=b""
            )
            with patch.object(clipboard, "_clipboard_info", return_value="furl"):
                self.assertEqual(clipboard.read_file_urls(), [str(image)])


if __name__ == "__main__":
    unittest.main()
