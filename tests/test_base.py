"""Shared backend command behavior."""

import subprocess
import unittest
from unittest.mock import patch

from pasteimg_lib.backends.base import BackendError, Clipboard


class ClipboardRunTest(unittest.TestCase):
    @patch("pasteimg_lib.backends.base.subprocess.run")
    def test_run_captures_output_by_default(self, run):
        expected = subprocess.CompletedProcess(["tool"], 0, stdout=b"out", stderr=b"")
        run.return_value = expected

        result = Clipboard._run(["tool"], stdin=b"input")

        self.assertIs(result, expected)
        run.assert_called_once_with(
            ["tool"], input=b"input", capture_output=True, check=False
        )

    @patch("pasteimg_lib.backends.base.subprocess.run")
    def test_run_reports_exit_code_when_stderr_is_empty(self, run):
        run.return_value = subprocess.CompletedProcess(
            ["tool"], 9, stdout=b"", stderr=b""
        )

        with self.assertRaisesRegex(BackendError, r"tool failed: exit 9"):
            Clipboard._run(["tool"])

    @patch("pasteimg_lib.backends.base.subprocess.run", side_effect=FileNotFoundError)
    def test_run_wraps_missing_command(self, run):
        with self.assertRaisesRegex(BackendError, r"tool not found"):
            Clipboard._run(["tool"])


if __name__ == "__main__":
    unittest.main()
