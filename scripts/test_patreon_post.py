"""Patreon formatting and desktop clipboard routing; no real clipboard touched."""
import os
import subprocess
import unittest
from unittest.mock import patch

import patreon_post


class FormattingTests(unittest.TestCase):
    def test_unicode_preview_declares_utf8(self):
        preview = patreon_post.render_preview(
            "What’s Inside", "<h1>Mark 7:14–8:10</h1>", ["heart"])
        self.assertIn('<meta charset="utf-8">', preview)
        self.assertIn("What’s Inside", preview)
        self.assertIn("Mark 7:14–8:10", preview)
        self.assertIn("<!doctype html>", preview)

    def test_sections_are_h1_and_reading_is_linked_once(self):
        body = """## Daily prayer
Please guide us.

## Mark 7:14–8:10
> [!bible]- [Mark 7:14-8:10 - WEB-OFFLINE](https://example.com/reading)
> [[Mark 7#^14|14]]. Verse dump.
 %% #Mark %%>
 [[Mark]] [[Mark 7]]

Our reflection.
## Daily question
What is happening “in” you?
"""
        result = patreon_post.build_body(body)
        self.assertIn("<h1>Daily prayer</h1>", result)
        self.assertIn("<h1>Daily question</h1>", result)
        self.assertIn('<h1><a href="https://example.com/reading">Mark 7:14–8:10</a></h1>', result)
        self.assertEqual(result.count("Mark 7:14"), 1)
        self.assertNotIn("Verse dump", result)
        self.assertNotIn("<h3>", result)
        self.assertNotIn("<h4>", result)
        self.assertIn("Our reflection.", result)

    def test_callout_without_preceding_heading_is_h1(self):
        result = patreon_post.build_body(
            "> [!bible]- [Mark 8:1-10 - WEB-OFFLINE](https://example.com/reading)\n"
            " %% #Mark %%>\nReflection.")
        self.assertIn('<h1><a href="https://example.com/reading">Mark 8:1-10</a></h1>', result)

    def test_source_heading_keeps_ascii_verse_range(self):
        result = patreon_post.build_body(
            "## Mark 8:1-10\n"
            "> [!bible]- [Mark 8:1-10 - WEB-OFFLINE](https://example.com/reading)\n"
            " %% #Mark %%>")
        self.assertIn('>Mark 8:1-10</a></h1>', result)


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
