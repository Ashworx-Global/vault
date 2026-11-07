"""Regression tests for headings rendered from Daily notes."""

import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("build_site", Path(__file__).with_name("build-site.py"))
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


class DailyHeadingTests(unittest.TestCase):
    def test_daily_section_headings_are_h2_without_extra_h1(self):
        body = "# Prayer\n## Reading\n### Detail\n#### Reflection\n##### Aside"
        html = build_site.render_blocks(body, {}, "", set(), daily_headings=True)
        self.assertEqual(
            html.splitlines(),
            ["<h2>Prayer</h2>", "<h2>Reading</h2>", "<h3>Detail</h3>",
             "<h2>Reflection</h2>", "<h5>Aside</h5>"],
        )
        self.assertNotIn("<h1>", html)

    def test_other_pages_keep_markdown_heading_levels(self):
        html = build_site.render_blocks("# Title\n## Section\n#### Detail", {}, "", set())
        self.assertEqual(html.splitlines(), ["<h1>Title</h1>", "<h2>Section</h2>", "<h4>Detail</h4>"])


if __name__ == "__main__":
    unittest.main()
