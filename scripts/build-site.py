#!/usr/bin/env python3
"""Build a modern static site from the Obsidian vault — stdlib only, no npm.

Reads:
  Daily/*.md          daily reading notes (Obsidian markdown + verse inserts)
  Bible/*.md          harvested verse pages (one file per passage)

Writes:
  site/dist/**        static HTML ready for GitHub Pages (Tailwind via CDN)

Linking parity with Obsidian:
  [[Zechariah 9 v 9]] / [[Zechariah 9 v 9|Behold...]] -> /bible/<slug>/
  [[2026-09-26 (Unexpected Opportunities)]]          -> /daily/<slug>/
  [[Zechariah 8#^1|1]] (block anchor)                -> span (no page) or book page
  [Zec 8:8](https://ref.ly/...)  (Logos)             -> external link, target=_blank
    (kept as-is so the Logos app / ref.ly can open the user's own copy)

Usage:
  python3 scripts/build-site.py [--base /vault] [--out site/dist]
"""

from __future__ import annotations

import html
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parent.parent
DAILY_DIR = REPO / "Daily"
BIBLE_DIR = REPO / "Bible"

SITE_NAME = "Man of God Daily Readings"
SITE_URL = "https://ashworx-global.github.io/vault"
VERSE = "Not by might, nor by power, but by my Spirit, says the Lord of hosts. — Zechariah 4:6"


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw, body = parts[1], parts[2]
            fm: dict = {"tags": [], "aliases": []}
            cur = None
            for line in raw.splitlines():
                s = line.strip()
                if s.startswith("tags:"):
                    cur = "tags"
                    continue
                if s.startswith("aliases:"):
                    cur = "aliases"
                    continue
                if s.startswith("cssclasses:"):
                    cur = None
                    continue
                if s.startswith("- ") and cur in ("tags", "aliases"):
                    fm[cur].append(s[2:].strip().strip('"').strip("'"))
                    continue
                if ":" in s and not s.startswith("-"):
                    cur = None
            return fm, body.lstrip("\n")
    return {"tags": [], "aliases": []}, text


# ---------------------------------------------------------------- slugs/urls

def slugify(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def page_url(kind: str, slug: str, base: str) -> str:
    return f"{base}/{kind}/{slug}/"


# ---------------------------------------------------------------- inline md

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
OBSIDIAN_COMMENT_RE = re.compile(r"%%.*?%%", re.DOTALL)
CODE_SPAN_RE = re.compile(r"`([^`]+)`")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|_(.+?)_")


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def render_inline(text: str, linkmap: dict, base: str, books: set[str]) -> str:
    text = OBSIDIAN_COMMENT_RE.sub("", text)
    # code spans -> placeholders so inner markup is untouched
    codes: list[str] = []

    def _code(m: re.Match) -> str:
        codes.append(f"<code>{esc(m.group(1))}</code>")
        return f"\ue000{len(codes) - 1}\ue001"

    text = CODE_SPAN_RE.sub(_code, esc(text))

    # images
    text = IMAGE_RE.sub(
        lambda m: f'<img src="{esc(m.group(2))}" alt="{m.group(1)}" loading="lazy" class="rounded-lg shadow-sm my-6 max-w-full">',
        text,
    )

    # wikilinks [[target|alias]] / [[target#anchor|alias]]
    def _wiki(m: re.Match) -> str:
        raw = m.group(1).strip()
        alias = raw
        if "|" in raw:
            raw, alias = raw.split("|", 1)
            raw, alias = raw.strip(), alias.strip()
        anchor = ""
        if "#" in raw:
            raw, anchor = raw.split("#", 1)
            raw = raw.strip()
        key = raw.lower()
        url = linkmap.get(key) or linkmap.get(slugify(raw))
        if url is None and raw.lower() in books:
            url = f"{base}/books/{slugify(raw)}/"
        if url:
            href = url + (f"#{quote(anchor)}" if anchor else "")
            return f'<a class="wikilink" href="{href}">{alias}</a>'
        return f'<span class="wikilink-unresolved" title="No page for {raw} in this vault">{alias}</span>'

    text = WIKILINK_RE.sub(_wiki, text)

    # markdown links — Logos/ref.ly stay external so the reader's own copy opens
    def _link(m: re.Match) -> str:
        label, href = m.group(1), m.group(2).strip()
        h = esc(href)
        if "ref.ly" in href or href.startswith("https://www.biblegateway.com"):
            return f'<a class="ext" href="{h}" target="_blank" rel="noopener noreferrer">{label}<span aria-hidden="true"> ↗</span></a>'
        if href.startswith("http"):
            return f'<a class="ext" href="{h}" target="_blank" rel="noopener noreferrer">{label}</a>'
        return f'<a class="wikilink" href="{h}">{label}</a>'

    text = LINK_RE.sub(_link, text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)

    def _it(m: re.Match) -> str:
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        return f"<em>{inner}</em>"

    text = ITALIC_RE.sub(_it, text)
    for i, c in enumerate(codes):
        text = text.replace(f"\ue000{i}\ue001", c)
    return text


# ---------------------------------------------------------------- blocks

def render_blocks(body: str, linkmap: dict, base: str, books: set[str]) -> str:
    lines = body.splitlines()
    out: list[str] = []
    i = 0
    in_fence = False
    fence_buf: list[str] = []

    def para(buf: list[str]) -> None:
        if not buf:
            return
        text = " ".join(s.strip() for s in buf)
        if not text:
            return
        m = re.match(r"\*\*(\d+[a-z]?)\*\*\s?(.*)$", text)
        if m:
            out.append(
                f'<p class="verse"><span class="verse-num">{m.group(1)}</span>'
                f'<span>{render_inline(m.group(2), linkmap, base, books)}</span></p>'
            )
        else:
            out.append(f"<p>{render_inline(text, linkmap, base, books)}</p>")

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if s.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_buf = []
            else:
                in_fence = False
                out.append(f"<pre><code>{esc(chr(10).join(fence_buf))}</code></pre>")
            i += 1
            continue
        if in_fence:
            fence_buf.append(line)
            i += 1
            continue
        if not s:
            i += 1
            continue
        if re.match(r"^#{1,6}\s", s):
            level = len(s) - len(s.lstrip("#"))
            out.append(f"<h{level}>{render_inline(s[level:].strip(), linkmap, base, books)}</h{level}>")
            i += 1
            continue
        if re.match(r"^(\*\*\*|---|___)\s*$", s):
            out.append("<hr>")
            i += 1
            continue
        # tables
        if "|" in s and i + 1 < len(lines) and re.match(r"^\|?[\s:|\-]+\|?\s*$", lines[i + 1].strip()):
            headers = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{render_inline(c, linkmap, base, books)}</th>" for c in headers)
            tr = "".join(
                "<tr>" + "".join(f"<td>{render_inline(c, linkmap, base, books)}</td>" for c in r) + "</tr>"
                for r in rows
            )
            out.append(f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
            continue
        # lists
        if re.match(r"^([-*+]\s|\d+[.)]\s)", s):
            items: list[str] = []
            while i < len(lines) and re.match(r"^([-*+]\s|\d+[.)]\s|\s{2,}\S)", lines[i].strip() and lines[i]):
                m = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", lines[i].strip())
                items.append(render_inline(m.group(1) if m else lines[i].strip(), linkmap, base, books))
                i += 1
            out.append("<ul>" + "".join(f"<li>{c}</li>" for c in items) + "</ul>")
            continue
        # blockquotes / bible callouts
        if s.startswith(">"):
            buf: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            first = buf[0].strip() if buf else ""
            m = re.match(r"\[!bible\]-\s*\[([^\]]+)\]\(([^)]+)\)", first)
            if m:
                title, url = m.group(1), m.group(2)
                inner = "\n".join(buf[1:])
                inner_html = render_blocks(inner, linkmap, base, books)
                out.append(
                    "<details class=\"bible\" open>"
                    f"<summary><span>{esc(title)}</span>"
                    f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">BibleGateway ↗</a>'
                    "</summary>"
                    f'<div class="bible-body">{inner_html}</div>'
                    "</details>"
                )
            else:
                inner = "\n".join(buf)
                out.append(f"<blockquote>{render_blocks(inner, linkmap, base, books)}</blockquote>")
            continue
        # plain paragraph (collect wrapped lines)
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", ">", "-", "*", "```", "|")) and not re.match(r"^\d+[.)]\s", lines[i].strip()):
            buf.append(lines[i])
            i += 1
        para(buf)
    return "\n".join(out)


# ---------------------------------------------------------------- pages

CSS_EXTRA = """
body{font-family:Inter,system-ui,sans-serif}
.font-serif{font-family:Merriweather,Georgia,serif}
.prose-custom p{line-height:1.75;margin-bottom:1rem;color:#44403c}
.prose-custom a{color:#15803d;text-underline-offset:2px}
.prose-custom a:hover{text-decoration:underline}
.prose-custom blockquote{border-left:4px solid #4ade80;background:#f0fdf4;padding:.75rem 1.25rem;border-radius:0 .75rem .75rem 0;margin:1.25rem 0;font-style:italic;color:#3f3f46}
details.bible{border:1px solid #bfdbfe;background:#eff6ff;border-radius:.75rem;margin:1rem 0;overflow:hidden}
details.bible summary{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.8rem 1.1rem;font-weight:600;color:#1d4ed8;cursor:pointer;list-style:none}
details.bible summary::-webkit-details-marker{display:none}
details.bible .bible-body{padding:0 1.1rem 1.1rem}
p.verse{display:flex;gap:.7rem;background:#fffbeb;border-left:4px solid #fbbf24;padding:.55rem .9rem;border-radius:0 .6rem .6rem 0;margin:.5rem 0}
.verse-num{font-weight:700;color:#92400e;min-width:2ch}
.wikilink{color:#15803d;font-weight:500;text-underline-offset:2px}
.wikilink:hover{text-decoration:underline}
.wikilink-unresolved{color:#78716c;border-bottom:1px dotted #a8a29e}
a.ext{color:#1d4ed8;font-weight:500}
a.ext:hover{text-decoration:underline}
.tag{display:inline-block;background:#f5f5f4;border:1px solid #e7e5e4;color:#57534e;border-radius:9999px;padding:.15rem .7rem;font-size:.8rem;margin:.15rem .2rem}
.tag:hover{background:#dcfce7;color:#15803d;border-color:#bbf7d0}
.card{background:#fff;border:1px solid #e7e5e4;border-radius:1rem;padding:1.25rem;transition:box-shadow .2s,transform .2s}
.card:hover{box-shadow:0 10px 25px -12px rgba(0,0,0,.25);transform:translateY(-2px)}
.tablewrap{overflow-x:auto;margin:1rem 0}
table{width:100%;border-collapse:collapse;font-size:.95rem}
th,td{border:1px solid #e7e5e4;padding:.5rem .75rem;text-align:left}
th{background:#f5f5f4}
pre{background:#1c1917;color:#f5f5f4;border-radius:.75rem;padding:1rem;overflow-x:auto}
code{font-family:'JetBrains Mono',ui-monospace,monospace}
p code{background:#dcfce7;color:#14532d;padding:.1rem .35rem;border-radius:.35rem;font-size:.85em}
"""

BASE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@TITLE@@ | Man of God Daily Readings</title>
<meta name="description" content="@@DESC@@">
<link rel="icon" type="image/svg+xml" href="@@BASE@@/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:wght@400;700;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{colors:{primary:{DEFAULT:'#16a34a'}}}}}</script>
<style>@@CSS@@</style>
</head>
<body class="min-h-screen flex flex-col bg-stone-50 text-stone-800 antialiased">
<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 bg-green-700 text-white rounded-lg">Skip to content</a>
<header class="bg-white/90 backdrop-blur border-b border-stone-200 sticky top-0 z-40">
<nav class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4" aria-label="Main">
<a href="@@BASE@@/" class="flex items-center gap-2 font-serif font-bold text-lg text-stone-900"><span aria-hidden="true">✝</span><span>Man of God Daily Readings</span></a>
<div class="flex flex-wrap gap-4 text-sm font-medium text-stone-600">
<a class="hover:text-green-700" href="@@BASE@@/daily/">Daily</a>
<a class="hover:text-green-700" href="@@BASE@@/bible/">Bible</a>
<a class="hover:text-green-700" href="@@BASE@@/books/">Books</a>
<a class="hover:text-green-700" href="@@BASE@@/tags/">Topics</a>
<a class="hover:text-green-700" href="https://github.com/Ashworx-Global/vault" target="_blank" rel="noopener">GitHub</a>
</div>
</nav>
</header>
<main id="main" class="flex-1 w-full max-w-6xl mx-auto px-4 py-8">@@BODY@@</main>
<footer class="border-t border-stone-200 bg-white mt-8">
<div class="max-w-6xl mx-auto px-4 py-8 grid gap-6 md:grid-cols-3 text-sm text-stone-600">
<div><h3 class="font-semibold text-stone-900 mb-2">Man of God Daily Readings</h3><p>Daily Bible notes with linked verse pages. Wikilinks mirror Obsidian; Logos ref.ly links open in your own Logos copy.</p></div>
<div><h3 class="font-semibold text-stone-900 mb-2">Browse</h3><p><a class="hover:text-green-700" href="@@BASE@@/daily/">Daily notes</a> · <a class="hover:text-green-700" href="@@BASE@@/bible/">Verse pages</a> · <a class="hover:text-green-700" href="@@BASE@@/books/">Books</a> · <a class="hover:text-green-700" href="@@BASE@@/tags/">Topics</a></p></div>
<div><h3 class="font-semibold text-stone-900 mb-2">Source</h3><p><a class="hover:text-green-700" href="https://github.com/Ashworx-Global/vault" target="_blank" rel="noopener">Ashworx-Global/vault</a> · built from Obsidian markdown, stdlib only, no npm.</p></div>
</div>
</footer>
<script>
const q=document.getElementById('filter');
if(q){q.addEventListener('input',()=>{const s=q.value.toLowerCase();document.querySelectorAll('[data-search]').forEach(el=>{el.style.display=el.dataset.search.includes(s)?'':'none';});});}
</script>
</body>
</html>
"""


def parse_book_ref(stem: str) -> tuple[str, str, str]:
    # "<Book> <C> v <R>": "Zechariah 9 v 1–17" -> (Zechariah, 9, 1–17)
    m = re.match(r"^(.*)\s+(\d+)\s+v\s+(.+)$", stem)
    if not m:
        return stem, "", ""
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()


def main() -> int:
    base = "/vault"
    out = REPO / "site" / "dist"
    for a in sys.argv[1:]:
        if a.startswith("--base="):
            base = a.split("=", 1)[1].rstrip("/") or "/vault"
        elif a.startswith("--out="):
            p = a.split("=", 1)[1]
            out = Path(p) if os.path.isabs(p) else REPO / p
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
    if out.exists():
        shutil.rmtree(out)
    (out / "daily").mkdir(parents=True)
    (out / "bible").mkdir(parents=True)
    (out / "books").mkdir(parents=True)
    (out / "tags").mkdir(parents=True)

    daily_files = sorted(DAILY_DIR.glob("*.md")) if DAILY_DIR.exists() else []
    bible_files = sorted(BIBLE_DIR.glob("*.md")) if BIBLE_DIR.exists() else []

    pages: list[dict] = []
    linkmap: dict[str, str] = {}
    books: set[str] = set()

    for f in bible_files:
        stem = f.stem
        slug = slugify(stem)
        book, ch, vr = parse_book_ref(stem)
        if book:
            books.add(book.lower())
        url = page_url("bible", slug, base)
        linkmap[stem.lower()] = url
        linkmap[slug] = url
        fm, body = split_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        pages.append({"kind": "bible", "file": f, "stem": stem, "slug": slug, "url": url,
                      "title": stem, "fm": fm, "body": body, "book": book, "chapter": ch, "verse": vr})

    for f in daily_files:
        stem = f.stem
        slug = slugify(stem)
        url = page_url("daily", slug, base)
        linkmap[stem.lower()] = url
        linkmap[slug] = url
        fm, body = split_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        m = re.match(r"(\d{4}-\d{2}-\d{2})", stem)
        pages.append({"kind": "daily", "file": f, "stem": stem, "slug": slug, "url": url,
                      "title": re.sub(r"^\d{4}-\d{2}-\d{2}\s*", "", stem).strip("() "),
                      "fm": fm, "body": body, "date": m.group(1) if m else "",
                      "book": "", "chapter": "", "verse": ""})

    for p in pages:  # aliases resolve too
        for a in p["fm"].get("aliases", []):
            linkmap.setdefault(a.strip().lower(), p["url"])

    def render_page(title: str, desc: str, body_html: str) -> str:
        h = BASE_TMPL.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc[:160])).replace("@@BASE@@", base).replace("@@CSS@@", CSS_EXTRA).replace("@@BODY@@", body_html)
        return h

    def tag_pills(tags: list[str]) -> str:
        return "".join(f'<a class="tag" href="{base}/tags/{quote(slugify(t))}/">#{esc(t)}</a>' for t in tags)

    def write(rel: str, title: str, desc: str, body_html: str) -> str:
        d = out / rel
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_page(title, desc, body_html), encoding="utf-8")
        return f"{base}/{rel}/".replace("//", "/")

    daily = sorted([p for p in pages if p["kind"] == "daily"], key=lambda p: p.get("date", ""), reverse=True)
    bible = sorted([p for p in pages if p["kind"] == "bible"],
                   key=lambda p: (p["book"].lower(), int(p["chapter"]) if p["chapter"].isdigit() else 999, p["verse"]))

    by_book: dict[str, list[dict]] = {}
    for p in bible:
        by_book.setdefault(p["book"] or "Other", []).append(p)
    tag_index: dict[str, list[dict]] = {}
    for p in pages:
        for t in p["fm"].get("tags", []):
            tag_index.setdefault(t, []).append(p)

    def card_daily(p: dict) -> str:
        search = esc((p["title"] + " " + p.get("date", "") + " " + " ".join(p["fm"].get("tags", []))).lower())
        pills = tag_pills(p["fm"].get("tags", [])[:6])
        blurb = esc(re.sub(r"\s+", " ", re.sub(r"[#>*`\[\]]", "", p["body"]))[:180] + "…")
        return (f'<article class="card" data-search="{search}"><p class="text-sm text-green-700 font-medium">{esc(p.get("date",""))}</p>'
                f'<h3 class="font-serif text-xl font-bold mt-1"><a class="hover:text-green-700" href="{p["url"]}">{esc(p["title"])}</a></h3>'
                f'<p class="text-sm text-stone-600 mt-2">{blurb}</p><div class="mt-3">{pills}</div></article>')

    def card_verse(p: dict) -> str:
        search = esc((p["title"] + " " + " ".join(p["fm"].get("tags", []))).lower())
        pills = tag_pills(p["fm"].get("tags", [])[:4])
        blurb = esc(re.sub(r"\s+", " ", re.sub(r"[#>*`\[\]]", "", p["body"]))[:140] + "…")
        return (f'<article class="card" data-search="{search}"><h3 class="font-semibold"><a class="hover:text-green-700" href="{p["url"]}">{esc(p["title"])}</a></h3>'
                f'<p class="text-sm text-stone-600 mt-2">{blurb}</p><div class="mt-3">{pills}</div></article>')

    # ---- home
    stats = (f'<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
             f'<div class="card text-center"><p class="text-3xl font-bold">{len(daily)}</p><p class="text-sm text-stone-600">Daily notes</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold">{len(bible)}</p><p class="text-sm text-stone-600">Verse pages</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold">{len(by_book)}</p><p class="text-sm text-stone-600">Books</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold">{len(tag_index)}</p><p class="text-sm text-stone-600">Topics</p></div></div>')
    hero = (f'<section class="rounded-2xl p-8 md:p-12 text-white mb-8" style="background:linear-gradient(135deg,#15803d,#14532d)">'
            f'<h1 class="font-serif text-4xl md:text-5xl font-black leading-tight">Man of God<br>Daily Readings</h1>'
            f'<p class="mt-4 text-lg text-green-100 max-w-2xl">Daily Bible notes with linked verse pages — the same links you use in Obsidian, rendered for the web. Logos links open in your own Logos copy.</p>'
            f'<div class="mt-6 flex flex-wrap gap-3"><a class="bg-white text-green-800 font-semibold px-5 py-2.5 rounded-lg" href="{base}/daily/">Browse daily notes</a>'
            f'<a class="border border-green-200 px-5 py-2.5 rounded-lg font-semibold" href="{base}/bible/">Explore verse pages</a></div></section>'
            f'<blockquote class="bg-amber-50 border-l-4 border-amber-400 p-6 rounded-r-xl mb-8"><p class="font-serif text-xl md:text-2xl text-amber-900">“{esc(VERSE)}”</p></blockquote>'
            f'{stats}'
            f'<div class="flex items-center justify-between mt-10 mb-4"><h2 class="font-serif text-2xl font-bold">Recent daily notes</h2><a class="text-green-700 font-medium" href="{base}/daily/">View all →</a></div>'
            f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{"".join(card_daily(p) for p in daily[:6])}</div>'
            f'<div class="flex items-center justify-between mt-10 mb-4"><h2 class="font-serif text-2xl font-bold">Recent verse pages</h2><a class="text-green-700 font-medium" href="{base}/bible/">View all →</a></div>'
            f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">{"".join(card_verse(p) for p in bible[-8:][::-1])}</div>')
    write("", SITE_NAME, VERSE, hero)

    # ---- daily index + pages
    write("daily", "Daily notes", "Chronological daily Bible reading notes.",
          f'<h1 class="font-serif text-3xl font-black mb-2">Daily notes</h1><p class="text-stone-600 mb-6">Newest first. Open any note to read reflections, verse inserts, and harvested verse pages.</p>'
          f'<input id="filter" placeholder="Filter notes…" class="w-full md:max-w-sm border border-stone-300 rounded-lg px-4 py-2 mb-6">'
          f'<div class="grid gap-4 md:grid-cols-2">{"".join(card_daily(p) for p in daily)}</div>')
    for p in daily:
        html_body = render_blocks(p["body"], linkmap, base, {b for b in books})
        harvested = sorted({m.group(1).strip() for m in WIKILINK_RE.finditer(p["body"]) if " v " in m.group(1)})
        links = []
        for ref in harvested:
            u = linkmap.get(ref.lower()) or linkmap.get(slugify(ref))
            if u:
                links.append(f'<a class="tag" href="{u}">{esc(ref)}</a>')
        body_html = (f'<p class="text-sm text-green-700 font-medium">{esc(p.get("date",""))}</p>'
                     f'<h1 class="font-serif text-3xl md:text-4xl font-black mb-3">{esc(p["title"])}</h1>'
                     f'<div class="mb-6">{tag_pills(p["fm"].get("tags", []))}</div>'
                     f'<div class="prose-custom">{html_body}</div>'
                     + (f'<h2 class="font-serif text-2xl font-bold mt-10 mb-3">Harvested verse pages</h2><div>{"".join(links)}</div>' if links else "")
                     + f'<p class="mt-10 text-sm"><a class="text-green-700" href="{base}/daily/">← All daily notes</a></p>')
        write(f"daily/{p['slug']}", p["title"], p["title"], body_html)

    # ---- bible index + pages
    books_sorted = sorted(by_book)
    opts = "".join(f'<button data-book="{esc(slugify(b))}" class="tag">{esc(b)} ({len(by_book[b])})</button>' for b in books_sorted)
    write("bible", "Verse pages", "Every harvested verse page, grouped by book.",
          f'<h1 class="font-serif text-3xl font-black mb-2">Verse pages</h1><p class="text-stone-600 mb-4">{len(bible)} pages across {len(books_sorted)} books.</p>'
          f'<input id="filter" placeholder="Filter passages…" class="w-full md:max-w-sm border border-stone-300 rounded-lg px-4 py-2 mb-4">'
          f'<div class="flex flex-wrap gap-2 mb-6"><button data-book="all" class="tag">All</button>{opts}</div>'
          f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">' + "".join(
              f'<div data-search="{esc((p["title"] + " " + " ".join(p["fm"].get("tags", []))).lower())}" data-book="{esc(slugify(p["book"]))}">{card_verse(p)}</div>'
              for p in bible) + '</div>'
          + '<script>document.querySelectorAll("[data-book]").forEach(b=>b.addEventListener("click",()=>{const f=b.dataset.book;document.querySelectorAll("#main [data-book].card, #main div[data-book]").forEach(()=>{});document.querySelectorAll(".grid [data-book]").forEach(c=>{c.style.display=(f==="all"||c.dataset.book===f)?"":"none";});}));</script>')
    for p in bible:
        html_body = render_blocks(p["body"], linkmap, base, books)
        related = [q for q in by_book.get(p["book"], []) if q["slug"] != p["slug"] and q["chapter"] == p["chapter"]][:8]
        aliases = "".join(f"<li>{esc(a)}</li>" for a in p["fm"].get("aliases", []))
        body_html = (f'<p class="text-sm"><a class="text-green-700" href="{base}/bible/">Verse pages</a> / <a class="text-green-700" href="{base}/books/{slugify(p["book"])}/">{esc(p["book"])}</a></p>'
                     f'<h1 class="font-serif text-3xl md:text-4xl font-black mt-1 mb-3">{esc(p["title"])}</h1>'
                     f'<div class="mb-6">{tag_pills(p["fm"].get("tags", []))}</div>'
                     f'<div class="prose-custom">{html_body}</div>'
                     + (f'<div class="mt-6 p-4 bg-green-50 border border-green-100 rounded-xl"><h3 class="font-semibold text-green-900">Also known as</h3><ul class="list-disc ml-5 text-green-900">{aliases}</ul></div>' if aliases else "")
                     + ("".join(f'<h2 class="font-serif text-2xl font-bold mt-10 mb-3">More in {esc(p["book"])} {esc(p["chapter"])}</h2><div class="grid gap-3 md:grid-cols-2 lg:grid-cols-3">' + "".join(card_verse(q) for q in related) + "</div>" if related else "")))
        write(f"bible/{p['slug']}", p["title"], p["title"], body_html)

    # ---- books
    write("books", "Books", "Verse pages grouped by Bible book.",
          '<h1 class="font-serif text-3xl font-black mb-2">Books</h1><p class="text-stone-600 mb-6">Verse pages grouped by Bible book.</p><div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">'
          + "".join(f'<a class="card" href="{base}/books/{slugify(b)}/"><h3 class="font-bold">{esc(b.title()) if b.islower() else esc(b)}</h3><p class="text-sm text-stone-600">{len(by_book[b])} passages</p></a>' for b in books_sorted) + "</div>")
    for b in books_sorted:
        groups: dict[str, list[dict]] = {}
        for p in by_book[b]:
            groups.setdefault(p["chapter"] or "—", []).append(p)
        secs = ""
        for ch in sorted(groups, key=lambda c: int(c) if c.isdigit() else 999):
            items = "".join(f'<a class="card block" href="{q["url"]}"><strong>{esc(q["title"])}</strong><br><span class="text-sm text-stone-600">{" ".join(q["fm"].get("tags", [])[:4])}</span></a>' for q in groups[ch])
            secs += f'<section class="card mb-6"><h2 class="font-bold text-lg mb-3">{esc(b)} {esc(ch)}</h2><div class="grid gap-3 md:grid-cols-2">{items}</div></section>'
        write(f"books/{slugify(b)}", b, f"Verse pages in {b}", f'<p class="text-sm"><a class="text-green-700" href="{base}/books/">Books</a> / {esc(b)}</p><h1 class="font-serif text-3xl font-black mt-1 mb-4">{esc(b)}</h1>{secs}')

    # ---- tags
    write("tags", "Topics", "Browse by theme.",
          '<h1 class="font-serif text-3xl font-black mb-2">Topics</h1><p class="text-stone-600 mb-6">Themes from passages and reflections.</p><div class="flex flex-wrap gap-2">'
          + "".join(f'<a class="tag" href="{base}/tags/{slugify(t)}/">#{esc(t)} ({len(tag_index[t])})</a>' for t in sorted(tag_index)) + "</div>")
    for t, plist in tag_index.items():
        cards = "".join(card_daily(p) if p["kind"] == "daily" else card_verse(p) for p in plist)
        write(f"tags/{slugify(t)}", f"#{t}", f"Pages tagged {t}",
              f'<p class="text-sm"><a class="text-green-700" href="{base}/tags/">Topics</a> / #{esc(t)}</p><h1 class="font-serif text-3xl font-black mt-1 mb-4">#{esc(t)}</h1><div class="grid gap-4 md:grid-cols-2">{cards}</div>')

    # ---- misc
    (out / "404.html").write_text(render_page("Not found", "Page not found",
        '<div class="text-center py-16"><h1 class="font-serif text-5xl font-black">404</h1><p class="text-stone-600 mt-2">That page is not in this vault.</p><p class="mt-6"><a class="text-green-700 font-semibold" href="' + base + '/">← Home</a></p></div>'), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    fav = REPO / "public" / "favicon.svg"
    if fav.exists():
        shutil.copyfile(fav, out / "favicon.svg")
    urls = [f"{SITE_URL}{base}/"]
    for root, _, files in os.walk(out):
        for fn in files:
            if fn == "index.html":
                rel = os.path.relpath(os.path.join(root, fn), out)
                u = f"{SITE_URL}{base}/" + ("" if rel == "index.html" else rel[: -len("/index.html")] + "/")
                urls.append(u)
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                     + "".join(f"<url><loc>{esc(u)}</loc><lastmod>{date.today().isoformat()}</lastmod></url>" for u in sorted(set(urls))) + "</urlset>", encoding="utf-8")
    print(f"built {len(pages)} pages ({len(daily)} daily, {len(bible)} verse) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
