"""Desktop clipboard routing; no real clipboard or browser is touched."""
import os
import subprocess
import unittest
from unittest.mock import patch

import patreon_post


class ClipboardTests(unittest.TestCase):
    @patch("patreon_post.subprocess.run")
    def test_macos(self, run):
        with patch("patreon_post.sys.platform", "darwin"):
            patreon_post.copy_html("<p>Hello</p>")
        self.assertEqual(run.call_args.args[0][0], "osascript")

    @patch("patreon_post.subprocess.run")
    def test_wayland_prefers_html(self, run):
        with patch("patreon_post.sys.platform", "linux"), \
             patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}, clear=True), \
             patch("patreon_post.shutil.which", return_value="/usr/bin/wl-copy"):
            patreon_post.copy_html("<p>Grace</p>")
        self.assertEqual(run.call_args.args[0], ["wl-copy", "--type", "text/html"])
        self.assertEqual(run.call_args.kwargs["input"], b"<p>Grace</p>")
        self.assertEqual(run.call_args.kwargs["stdout"], subprocess.DEVNULL)

    @patch("patreon_post.subprocess.run")
    def test_x11_fallback(self, run):
        with patch("patreon_post.sys.platform", "linux"), \
             patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}, clear=True), \
             patch("patreon_post.shutil.which", side_effect=lambda name: name if name == "xclip" else None):
            patreon_post.copy_html("<p>Peace</p>")
        self.assertEqual(run.call_args.args[0],
                         ["xclip", "-selection", "clipboard", "-t", "text/html", "-i"])

    @patch("patreon_post.subprocess.run")
    def test_headless_does_not_invoke_clipboard(self, run):
        with patch("patreon_post.sys.platform", "linux"), \
             patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Linux HTML clipboard unavailable"):
                patreon_post.copy_html("<p>Hello</p>")
        run.assert_not_called()

    @patch("patreon_post.subprocess.run")
    def test_missing_tools(self, run):
        with patch("patreon_post.sys.platform", "linux"), \
             patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0", "DISPLAY": ":0"}, clear=True), \
             patch("patreon_post.shutil.which", return_value=None):
            with self.assertRaises(RuntimeError):
                patreon_post.copy_html("<p>Hello</p>")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
