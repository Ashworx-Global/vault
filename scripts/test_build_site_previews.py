"""Regression coverage for vault syntax leaking into reading cards."""

import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("build_site", Path(__file__).with_name("build-site.py"))
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


class PreviewTests(unittest.TestCase):
    def test_imported_passage_and_metadata_do_not_hide_reflection(self):
        body = """## Reading
> [!bible]- [Passage - WEB-OFFLINE](https://example.com)
> [[John 1#^1|1]]. Scripture text.

%% private metadata %%
[[John]] [[John 1]]

## Reflection
Read [[John 1 v 1|this passage]] and [reflect](https://example.com).
"""
        self.assertEqual(build_site.preview_text(body), "Read this passage and reflect.")

    def test_first_paragraph_is_not_joined_to_unrelated_sections(self):
        self.assertEqual(build_site.preview_text("A short prayer.\n\n## Reading\nAnother section."),
                         "A short prayer.")

    def test_truncation_uses_whole_words_and_only_adds_ellipsis_when_needed(self):
        self.assertEqual(build_site.preview_text("One two three four", 10), "One two…")
        self.assertEqual(build_site.preview_text("One two", 10), "One two")


if __name__ == "__main__":
    unittest.main()
