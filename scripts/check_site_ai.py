#!/usr/bin/env python3
"""Check the built site (site/dist) for AI discoverability and URL correctness.

Run after scripts/build-site.py. Exits 1 if any check fails, so it can gate a deploy.

Usage:
  python3 scripts/check_site_ai.py [--dist site/dist]

Checks:
  - required files exist (index, robots, sitemap, llms.txt, llms-full.txt, 404)
  - robots.txt allows the AI crawlers and names the sitemap
  - every page has a canonical link and parseable JSON-LD with an @graph
  - every daily, blog and resource URL in the sitemap is listed in llms.txt
  - llms-full.txt has no leftover wikilink or callout syntax
  - no pages point at the old /vault base path
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "CCBot"]
OLD_BASE = re.compile(r'(href|src)="/vault/|github\.io/vault|manofgod\.online/vault')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", default=str(REPO / "site" / "dist"))
    dist = Path(ap.parse_args().dist)
    failures: list[str] = []

    def fail(msg: str) -> None:
        failures.append(msg)

    for name in ["index.html", "robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt", "404.html"]:
        if not (dist / name).exists():
            fail(f"missing {name}")
    if failures:
        return report(failures, dist)

    robots = (dist / "robots.txt").read_text(encoding="utf-8")
    for bot in AI_BOTS:
        if f"User-agent: {bot}" not in robots:
            fail(f"robots.txt does not name {bot}")
    if "Sitemap: " not in robots:
        fail("robots.txt has no Sitemap line")

    pages = [p for p in dist.rglob("index.html")]
    for p in pages:
        rel = p.relative_to(dist).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        if OLD_BASE.search(text):
            fail(f"{rel} links to the old /vault base path")
        if rel == "404/index.html":
            continue
        if '<link rel="canonical" href="' not in text:
            fail(f"{rel} has no canonical link")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        if not blocks:
            fail(f"{rel} has no JSON-LD")
        for b in blocks:
            try:
                if "@graph" not in json.loads(b):
                    fail(f"{rel} JSON-LD has no @graph")
            except json.JSONDecodeError as e:
                fail(f"{rel} JSON-LD does not parse: {e}")

    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    guide = (dist / "llms.txt").read_text(encoding="utf-8")
    listed = [u for u in urls if re.search(r"/(daily|blog|resources)/[^/]+/$", u)]
    missing = [u for u in listed if u not in guide]
    for u in missing[:10]:
        fail(f"llms.txt does not list {u}")
    if len(missing) > 10:
        fail(f"llms.txt is missing {len(missing)} content URLs in total")

    about_src = REPO / "Pages" / "about.md"
    if about_src.exists():
        about_html = dist / "about" / "index.html"
        if not about_html.exists():
            fail("Pages/about.md exists but /about/ was not built")
        else:
            front = about_src.read_text(encoding="utf-8").split("---", 2)[1]
            named = re.search(r"^name:[ \t]*\S", front, re.M) is not None
            if named and '"@type": "Person"' not in about_html.read_text(encoding="utf-8"):
                fail("About page has a name but no Person structured data")
        if "/about/" not in guide:
            fail("llms.txt does not list the About page")

    full = (dist / "llms-full.txt").read_text(encoding="utf-8")
    for pattern, label in [(r"\[\[", "wikilink"), (r"\[!bible\]", "callout header")]:
        if re.search(pattern, full):
            fail(f"llms-full.txt contains leftover {label} syntax")

    return report(failures, dist, pages=len(pages), listed=len(listed))


def report(failures: list[str], dist: Path, pages: int = 0, listed: int = 0) -> int:
    if failures:
        print(f"FAILED {len(failures)} check(s) in {dist}:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"ok: {pages} pages checked, {listed} content URLs listed in llms.txt, AI crawlers allowed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
