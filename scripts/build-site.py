#!/usr/bin/env python3
"""Build a modern static site from the Obsidian vault — stdlib only, no npm.

Reads:
  Daily/*.md          daily reading notes (Obsidian markdown + verse inserts)
  Bible/*.md          harvested verse pages (one file per passage)
  Resources/*.md      recommended books / podcasts / YouTube channels (one file each,
                      files starting with _ are skipped; see Resources/_TEMPLATE.md)

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

import hashlib
import html
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlsplit

REPO = Path(__file__).resolve().parent.parent
DAILY_DIR = REPO / "Daily"
BIBLE_DIR = REPO / "Bible"
ART_DIR = REPO / "Art"
RESOURCE_DIR = REPO / "Resources"
SCRIPTURE_IMG_DIR = RESOURCE_DIR / "Scripture-Images"
PAGES_DIR = REPO / "Pages"

# Resource `type:` values and the label shown on the filter buttons
RESOURCE_TYPES = {"book": "Books", "podcast": "Podcasts", "youtube": "YouTube", "other": "Other"}

SITE_NAME = "Man of God Daily Readings"
SITE_URL = "https://ashworx-global.github.io/vault"
VERSE = "Not by might, nor by power, but by my Spirit, says the Lord of hosts. — Zechariah 4:6"

# ---------------------------------------------------------------- theme (matches shop)
THEME_CSS = """
:root {
  --color-ink: #0b0f14;
  --color-panel: #121821;
  --color-gold: #c8a24a;
  --color-gold-dark: #a8832f;
  --font-display: "Georgia", "Times New Roman", serif;
}
body { background: var(--color-ink); color: #e7e5e4; font-family: Inter, system-ui, sans-serif; }
.font-display { font-family: var(--font-display); }
.btn { display: inline-block; border-radius: .375rem; background: var(--color-gold); padding: .625rem 1.25rem; text-align: center; font-weight: 600; color: var(--color-ink); transition: background .2s; }
.btn:hover { background: var(--color-gold-dark); }
.btn:disabled { opacity: .5; }
.btn-sm { border-radius: .375rem; border: 1px solid var(--color-gold); background: transparent; padding: .375rem .75rem; font-size: .875rem; color: var(--color-gold); transition: all .2s; }
.btn-sm:hover { background: var(--color-gold); color: var(--color-ink); }
.input { width: 100%; border-radius: .375rem; border: 1px solid #3f3f46; background: var(--color-panel); padding: .5rem .75rem; color: #fafafa; }
.input:focus { border-color: var(--color-gold); outline: none; }
.card { border-radius: .5rem; border: 1px solid #292524; background: var(--color-panel); padding: 1.25rem; min-width: 0; }
.card p, .prose-custom p { overflow-wrap: anywhere; word-break: break-word; }
a { color: var(--color-gold); text-underline-offset: 2px; }
a:hover { text-decoration: underline; }
.wikilink { color: var(--color-gold); font-weight: 500; text-underline-offset: 2px; }
.wikilink:hover { text-decoration: underline; }
.wikilink-unresolved { color: #78716c; border-bottom: 1px dotted #a8a29e; }
a.ext { color: var(--color-gold); font-weight: 500; }
a.ext:hover { text-decoration: underline; }
.tag { display: inline-block; background: #292524; border: 1px solid #44403c; color: #d6d3d1; border-radius: 9999px; padding: .15rem .7rem; font-size: .8rem; margin: .15rem .2rem; text-decoration: none; }
.tag:hover { background: var(--color-gold); color: var(--color-ink); border-color: var(--color-gold); }
.tablewrap { overflow-x: auto; margin: 1rem 0; }
table { width: 100%; border-collapse: collapse; font-size: .95rem; }
th, td { border: 1px solid #292524; padding: .5rem .75rem; text-align: left; }
th { background: #1c1917; }
pre { background: #0b0f14; color: #fafafa; border-radius: .5rem; padding: 1rem; overflow-x: auto; }
code { font-family: 'JetBrains Mono', ui-monospace, monospace; }
p code { background: #1c1917; color: var(--color-gold); padding: .1rem .35rem; border-radius: .25rem; font-size: .85em; }
.prose-custom { line-height: 1.75; }
.prose-custom p { margin-bottom: 1rem; color: #d6d3d1; }
.prose-custom h1, .prose-custom h2, .prose-custom h3 { font-family: var(--font-display); color: #fafafa; }
.prose-custom blockquote { border-left: 4px solid var(--color-gold); background: rgba(200,162,74,.1); padding: .75rem 1.25rem; border-radius: 0 .75rem .75rem 0; margin: 1.25rem 0; font-style: italic; color: #d6d3d1; }
details.bible { border: 1px solid #292524; background: var(--color-panel); border-radius: .5rem; margin: 1rem 0; overflow: hidden; }
details.bible summary { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .8rem 1.1rem; font-weight: 600; color: var(--color-gold); cursor: pointer; list-style: none; }
details.bible summary::-webkit-details-marker { display: none; }
details.bible .bible-body { padding: 0 1.1rem 1.1rem; }
p.verse { display: flex; gap: .7rem; background: rgba(200,162,74,.1); border-left: 4px solid var(--color-gold); padding: .55rem .9rem; border-radius: 0 .6rem .6rem 0; margin: .5rem 0; }
.verse-num { font-weight: 700; color: var(--color-gold); min-width: 2ch; }
img { border-radius: .5rem; box-shadow: 0 1px 3px rgba(0,0,0,.3); margin: 1.5rem 0; max-width: 100%; }
[data-lightbox] { cursor: pointer; user-select: none; }
[data-lightbox]:hover { opacity: .9; }
#lightbox { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.95); z-index: 50; align-items: center; justify-content: center; }
#lightbox-img { max-width: 90%; max-height: 90vh; border-radius: .5rem; user-select: none; pointer-events: none; }
.lightbox-nav { position: absolute; top: 50%; transform: translateY(-50%); background: rgba(200,162,74,.2); border: 1px solid var(--color-gold); color: var(--color-gold); padding: .5rem .75rem; cursor: pointer; border-radius: .25rem; font-size: 1.5rem; user-select: none; }
.lightbox-nav:hover { background: rgba(200,162,74,.4); }
#lightbox-prev { left: 1rem; }
#lightbox-next { right: 1rem; }
#lightbox-close { position: absolute; top: 1rem; right: 1rem; background: rgba(200,162,74,.2); border: 1px solid var(--color-gold); color: var(--color-gold); width: 2rem; height: 2rem; border-radius: .25rem; display: flex; align-items: center; justify-content: center; cursor: pointer; user-select: none; }
#lightbox-close:hover { background: rgba(200,162,74,.4); }
footer { border-top: 1px solid #292524; background: var(--color-panel); }
header img { margin: 0; box-shadow: none; }
@media (max-width: 640px) { header { position: static; } main { overflow-wrap: anywhere; } details.bible summary { flex-wrap: wrap; } p.verse { padding: .5rem .7rem; } h1 { overflow-wrap: anywhere; } }
header { background: rgba(18,24,33,.95); backdrop-filter: blur(8px); border-bottom: 1px solid #292524; position: sticky; top: 0; z-index: 40; }
"""

BASE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@TITLE@@ | Man of God Daily Readings</title>
<meta name="description" content="@@DESC@@">
<link rel="icon" type="image/png" sizes="32x32" href="@@BASE@@/logos/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="@@BASE@@/logos/favicon-64.png">
<link rel="apple-touch-icon" href="@@BASE@@/logos/icon-256.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<style>@@THEME_CSS@@</style>
</head>
<body class="min-h-screen flex flex-col antialiased">
<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 bg-gold text-ink rounded-lg">Skip to content</a>
<header>
<nav class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-2 md:py-0">
<a href="@@BASE@@/" class="flex items-center shrink-0"><img src="@@BASE@@/logos/icon-256.png" alt="Man Of God" class="h-16 md:h-28 w-auto"></a>
<div class="flex flex-wrap items-center justify-end gap-x-4 gap-y-2 text-sm md:gap-5">
<a href="@@BASE@@/daily/" class="hover:text-gold transition">Daily</a>
<a href="@@BASE@@/bible/" class="hover:text-gold transition">Bible</a>
<a href="@@BASE@@/books/" class="hover:text-gold transition">Books</a>
<a href="@@BASE@@/tags/" class="hover:text-gold transition">Topics</a>
<a href="@@BASE@@/art/" class="hover:text-gold transition">Art</a>
<a href="@@BASE@@/resources/" class="hover:text-gold transition">Resources</a>
<a href="@@BASE@@/graph/" class="hover:text-gold transition">Graph</a>
<a href="@@BASE@@/shop/" class="btn-sm">Shop</a>
<a href="https://github.com/Ashworx-Global/vault" target="_blank" rel="noopener" class="btn-sm">GitHub</a>
<a href="https://www.patreon.com/cw/ManOfGodSA" target="_blank" rel="noopener" class="btn-sm">Patreon</a>
<a href="https://www.facebook.com/profile.php?id=61596013522180" target="_blank" rel="noopener" class="btn-sm">Facebook</a>
</div>
</nav>
</header>
<main id="main" class="flex-1 w-full max-w-6xl mx-auto px-4 py-8">@@BODY@@</main>
<footer>
<div class="max-w-6xl mx-auto px-4 py-8 grid gap-6 md:grid-cols-3 text-sm" style="color: #a8a29e;">
<div><h3 class="font-display text-gold mb-2">Man of God Daily Readings</h3><p>A GitHub Pages site rendered from an <a class="hover:text-gold" href="https://obsidian.md/" target="_blank" rel="noopener">Obsidian</a> vault of daily Bible notes. Verse links mirror the vault's wikilinks, and scripture text comes from the ESV via the <a class="hover:text-gold" href="https://api.esv.org/" target="_blank" rel="noopener">Crossway API</a>. Logos links open each passage in your own Logos library — <a class="hover:text-gold" href="https://www.logos.com/free-edition" target="_blank" rel="noopener">get Logos free</a>.</p></div>
<div><h3 class="font-display text-gold mb-2">Browse</h3><p><a class="hover:text-gold" href="@@BASE@@/daily/">Daily notes</a> · <a class="hover:text-gold" href="@@BASE@@/bible/">Verse pages</a> · <a class="hover:text-gold" href="@@BASE@@/books/">Books</a> · <a class="hover:text-gold" href="@@BASE@@/tags/">Topics</a> · <a class="hover:text-gold" href="@@BASE@@/art/">Art</a> · <a class="hover:text-gold" href="@@BASE@@/resources/">Resources</a> · <a class="hover:text-gold" href="@@BASE@@/graph/">Graph</a></p></div>
<div><h3 class="font-display text-gold mb-2">Source</h3><p><a class="hover:text-gold" href="https://github.com/Ashworx-Global/vault" target="_blank" rel="noopener">Ashworx-Global/vault</a> · built from Obsidian markdown, stdlib only, no npm.</p></div>
</div>
</footer>
<div id="lightbox">
  <button id="lightbox-close">✕</button>
  <button id="lightbox-prev" class="lightbox-nav">‹</button>
  <img id="lightbox-img" src="" alt="Enlarged view" style="user-select: none;" data-no-save />
  <button id="lightbox-next" class="lightbox-nav">›</button>
</div>
<script>
const q=document.getElementById('filter');
if(q){q.addEventListener('input',()=>{const s=q.value.toLowerCase();document.querySelectorAll('[data-search]').forEach(el=>{el.style.display=el.dataset.search.includes(s)?'':'none';});});}
// Lightbox for art gallery
document.addEventListener('DOMContentLoaded',()=>{
  const lightbox=document.getElementById('lightbox');
  const lightboxImg=document.getElementById('lightbox-img');
  const lightboxClose=document.getElementById('lightbox-close');
  const lightboxPrev=document.getElementById('lightbox-prev');
  const lightboxNext=document.getElementById('lightbox-next');
  if(!lightbox)return;
  let currentIdx=0,images=[];
  document.querySelectorAll('[data-lightbox]').forEach((el,idx)=>{
    el.addEventListener('click',(e)=>{e.preventDefault();currentIdx=idx;showImage();});
    images.push(el.dataset.lightbox);
  });
  function showImage(){
    lightboxImg.src=images[currentIdx];
    lightbox.style.display='flex';
  }
  function closeBox(){lightbox.style.display='none';}
  lightboxClose?.addEventListener('click',closeBox);
  lightboxPrev?.addEventListener('click',()=>{currentIdx=(currentIdx-1+images.length)%images.length;showImage();});
  lightboxNext?.addEventListener('click',()=>{currentIdx=(currentIdx+1)%images.length;showImage();});
  lightbox?.addEventListener('click',(e)=>{if(e.target===lightbox)closeBox();});
  document.addEventListener('keydown',(e)=>{if(lightbox.style.display==='flex'){
    if(e.key==='Escape')closeBox();
    if(e.key==='ArrowLeft')lightboxPrev?.click();
    if(e.key==='ArrowRight')lightboxNext?.click();
  }});
});
// Prevent right-click on gallery images
document.addEventListener('contextmenu',(e)=>{if(e.target.closest('[data-lightbox]')||e.target.closest('[data-no-save]'))e.preventDefault();});
// Prevent drag-save
document.addEventListener('dragstart',(e)=>{if(e.target.closest('[data-lightbox]')||e.target.closest('[data-no-save]'))e.preventDefault();});
</script>
</body>
</html>
"""

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


def parse_resource(path: Path) -> dict | None:
    """Parse one Resources/*.md file (frontmatter + markdown summary).

    Frontmatter keys: title, type (book|podcast|youtube|other), by, image (path relative
    to Resources/), links (list of `Label: https://...`), tags (list). Only http(s) links
    are kept, and the image must exist inside Resources/. Returns None if the file has no
    frontmatter.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        print(f"  ⚠ {path.name}: no frontmatter, skipped")
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"  ⚠ {path.name}: unterminated frontmatter, skipped")
        return None
    fm: dict = {"links": [], "tags": []}
    cur = None
    for line in parts[1].splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("- ") and cur in ("links", "tags"):
            fm[cur].append(s[2:].strip().strip('"').strip("'"))
        elif ":" in s:
            key, val = s.split(":", 1)
            key, val = key.strip().lower(), val.strip().strip('"').strip("'")
            cur = key if key in ("links", "tags") else None
            if cur is None:
                fm[key] = val
    links = []
    for raw in fm["links"]:
        label, sep, url = raw.partition(": ")
        if not sep:
            label, url = urlsplit(raw).netloc, raw
        if urlsplit(url.strip()).scheme in ("http", "https"):
            links.append((label.strip(), url.strip()))
        else:
            print(f"  ⚠ {path.name}: link '{raw}' is not an http(s) URL, skipped")
    image = None
    if fm.get("image"):
        cand = (RESOURCE_DIR / fm["image"]).resolve()
        if cand.is_file() and RESOURCE_DIR.resolve() in cand.parents:
            image = cand
        else:
            print(f"  ⚠ {path.name}: image '{fm['image']}' not found in Resources/, skipped")
    rtype = fm.get("type", "other").lower()
    return {"slug": slugify(path.stem), "title": fm.get("title") or path.stem,
            "type": rtype if rtype in RESOURCE_TYPES else "other", "by": fm.get("by", ""),
            "image": image, "links": links, "tags": fm["tags"], "body": parts[2].lstrip("\n")}


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
                    "<details class=\"bible\">"
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
.card{min-width:0}
.card p,.prose-custom p{overflow-wrap:anywhere;word-break:break-word}
.tablewrap{overflow-x:auto;margin:1rem 0}
table{width:100%;border-collapse:collapse;font-size:.95rem}
th,td{border:1px solid #e7e5e4;padding:.5rem .75rem;text-align:left}
th{background:#f5f5f4}
pre{background:#1c1917;color:#f5f5f4;border-radius:.75rem;padding:1rem;overflow-x:auto}
code{font-family:'JetBrains Mono',ui-monospace,monospace}
p code{background:#dcfce7;color:#14532d;padding:.1rem .35rem;border-radius:.35rem;font-size:.85em}
"""


def parse_book_ref(stem: str) -> tuple[str, str, str]:
    # "<Book> <C> v <R>": "Zechariah 9 v 1–17" -> (Zechariah, 9, 1–17)
    m = re.match(r"^(.*)\s+(\d+)\s+v\s+(.+)$", stem)
    if not m:
        return stem, "", ""
    return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()


# ---------------------------------------------------------------- graph

GRAPH_COLORS = {"daily": "#16a34a", "verse": "#f59e0b", "book": "#2563eb", "tag": "#78716c", "concept": "#c4b5a5"}
GRAPH_DEFAULT_ON = ("verse", "tag")  # node types shown on first load; the rest start unticked
GRAPH_DEFAULT_QUERY = "grace"  # prefilled search: highlights matches and their neighbours
GRAPH_LABELS = {"daily": "Daily notes", "verse": "Verse pages", "book": "Books", "tag": "Topics", "concept": "Unlinked concepts"}


def build_graph(pages: list[dict], linkmap: dict, books: set[str], tag_index: dict, base: str) -> dict:
    """Nodes + edges from wikilinks and tags, the same relationships Obsidian's graph shows.

    Wikilinks to a real page link page-to-page; to a Bible book (or "Book 8" chapter
    refs) link to the book node; anything else becomes a "concept" node (Obsidian's
    unresolved-link ghost), because names like [[Zerubbabel]] are the real connective tissue.
    """
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str]] = set()
    url_to_id = {p["url"]: f'{p["kind"]}:{p["slug"]}' for p in pages}

    def add(nid: str, label: str, kind: str, url: str = "") -> str:
        nodes.setdefault(nid, {"id": nid, "label": label, "type": kind, "url": url})
        return nid

    for p in pages:
        kind = "daily" if p["kind"] == "daily" else "verse"
        add(url_to_id[p["url"]], p["title"], kind, p["url"])
    for t in tag_index:
        add(f"tag:{slugify(t)}", f"#{t}", "tag", f"{base}/tags/{quote(slugify(t))}/")

    def target(raw: str) -> str | None:
        key = raw.strip().lower()
        url = linkmap.get(key) or linkmap.get(slugify(raw))
        if url:
            return url_to_id.get(url)
        m = re.match(r"^(.*?)(?:\s+\d+)?$", raw.strip())
        book = (m.group(1) if m else raw).strip()
        if book.lower() in books:
            return add(f"book:{slugify(book)}", book, "book", f"{base}/books/{slugify(book)}/")
        return add(f"concept:{slugify(raw)}", raw.strip(), "concept") if slugify(raw) else None

    for p in pages:
        src = url_to_id[p["url"]]
        for m in WIKILINK_RE.finditer(OBSIDIAN_COMMENT_RE.sub("", p["body"])):
            raw = m.group(1).split("|", 1)[0].split("#", 1)[0]
            dst = target(raw)
            if dst and dst != src:
                edges.add(tuple(sorted((src, dst))))
        for t in p["fm"].get("tags", []):
            edges.add(tuple(sorted((src, f"tag:{slugify(t)}"))))
        if p["kind"] == "bible" and p["book"]:  # every verse page belongs to its book
            edges.add(tuple(sorted((src, target(p["book"])))))

    degree: dict[str, int] = {}
    for a, b in edges:
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    live = [n for n in nodes.values() if degree.get(n["id"])]  # drop orphans
    for n in live:
        n["deg"] = degree[n["id"]]
    return {"nodes": live, "links": [list(e) for e in sorted(edges)]}


GRAPH_JS = r"""
(function(){
const data=JSON.parse(document.getElementById('graph-data').textContent);
const COLORS=@@COLORS@@, LABELS=@@LABELS@@;
const cv=document.getElementById('graph'), ctx=cv.getContext('2d');
const tip=document.getElementById('graph-tip');
const nodes=data.nodes.map((n,i)=>({...n,i,x:Math.cos(i)*200+Math.random()*50,y:Math.sin(i)*200+Math.random()*50,vx:0,vy:0,r:4+Math.sqrt(n.deg)*2.2}));
const byId=new Map(nodes.map(n=>[n.id,n]));
const links=data.links.map(([a,b])=>({s:byId.get(a),t:byId.get(b)})).filter(l=>l.s&&l.t);
const adj=new Map(nodes.map(n=>[n,new Set()]));
links.forEach(l=>{adj.get(l.s).add(l.t);adj.get(l.t).add(l.s);});
const visibleTypes=new Set([...document.querySelectorAll('[data-gtype]')].filter(c=>c.checked).map(c=>c.dataset.gtype));
let query=document.getElementById('graph-search').value.trim().toLowerCase(),hover=null,drag=null,alpha=1,W=0,H=0,dpr=1,view={x:0,y:0,k:1},panning=null;
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;

function resize(){const r=cv.getBoundingClientRect();dpr=devicePixelRatio||1;W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;if(!view.set){view.x=W/2;view.y=H/2;view.set=true;}draw();}
function vis(n){return visibleTypes.has(n.type)&&(!query||n.label.toLowerCase().includes(query));}
function matchSet(){if(!query)return null;const m=new Set();nodes.filter(vis).forEach(n=>{m.add(n);adj.get(n).forEach(x=>m.add(x));});return m;}

function tick(){
  const vn=nodes.filter(n=>visibleTypes.has(n.type));
  for(let a=0;a<vn.length;a++){const p=vn[a];
    p.vx-=p.x*0.004;p.vy-=p.y*0.004; // gentle pull to centre
    for(let b=a+1;b<vn.length;b++){const q=vn[b];let dx=p.x-q.x,dy=p.y-q.y,d2=dx*dx+dy*dy+0.01;
      if(d2>90000)continue;const f=900/d2,d=Math.sqrt(d2);dx=dx/d*f;dy=dy/d*f;p.vx+=dx;p.vy+=dy;q.vx-=dx;q.vy-=dy;}}
  links.forEach(l=>{if(!visibleTypes.has(l.s.type)||!visibleTypes.has(l.t.type))return;
    const dx=l.t.x-l.s.x,dy=l.t.y-l.s.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-60)*0.02*alpha+ (d-60)*0.01;
    const fx=dx/d*f,fy=dy/d*f;l.s.vx+=fx;l.s.vy+=fy;l.t.vx-=fx;l.t.vy-=fy;});
  vn.forEach(n=>{if(n===drag)return;n.vx*=0.82;n.vy*=0.82;n.x+=n.vx*alpha;n.y+=n.vy*alpha;});
  alpha=Math.max(alpha*0.992,0.02);
}

function draw(){
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);
  ctx.translate(view.x,view.y);ctx.scale(view.k,view.k);
  const focus=hover||null,ms=matchSet();
  const lit=n=>!focus?(!ms||ms.has(n)):(n===focus||adj.get(focus).has(n));
  ctx.lineWidth=1/view.k;
  links.forEach(l=>{if(!visibleTypes.has(l.s.type)||!visibleTypes.has(l.t.type))return;
    const on=focus?(l.s===focus||l.t===focus):(!ms||(ms.has(l.s)&&ms.has(l.t)));
    ctx.strokeStyle=on?(focus?'rgba(21,128,61,.75)':'rgba(120,113,108,.35)'):'rgba(120,113,108,.07)';
    ctx.beginPath();ctx.moveTo(l.s.x,l.s.y);ctx.lineTo(l.t.x,l.t.y);ctx.stroke();});
  nodes.forEach(n=>{if(!visibleTypes.has(n.type))return;
    ctx.globalAlpha=lit(n)?1:0.15;ctx.fillStyle=COLORS[n.type];
    ctx.beginPath();ctx.arc(n.x,n.y,n.r,0,6.2832);ctx.fill();
    if(n===focus){ctx.lineWidth=2/view.k;ctx.strokeStyle='#1c1917';ctx.stroke();}});
  ctx.globalAlpha=1;ctx.font=`${11/Math.max(view.k,0.6)}px Inter,system-ui,sans-serif`;ctx.textAlign='center';ctx.fillStyle='#44403c';
  nodes.forEach(n=>{if(!visibleTypes.has(n.type)||!lit(n))return;
    const show=n===focus||(focus&&adj.get(focus).has(n))||(ms&&ms.has(n))||(!focus&&!ms&&(n.deg>=8||view.k>1.8));
    if(show)ctx.fillText(n.label.length>34?n.label.slice(0,33)+'…':n.label,n.x,n.y+n.r+12/Math.max(view.k,0.6));});
}

let raf=0;function loop(){if(!reduce&&alpha>0.021)tick();draw();raf=requestAnimationFrame(loop);}
if(reduce){for(let i=0;i<400;i++)tick();alpha=0.02;}

function toWorld(e){const r=cv.getBoundingClientRect();return{x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k};}
function pick(e){const p=toWorld(e);let best=null,bd=1e9;nodes.forEach(n=>{if(!visibleTypes.has(n.type))return;const d=Math.hypot(n.x-p.x,n.y-p.y);if(d<n.r+4/view.k&&d<bd){best=n;bd=d;}});return best;}
let moved=false;
cv.addEventListener('pointerdown',e=>{cv.setPointerCapture(e.pointerId);moved=false;const n=pick(e);if(n){drag=n;alpha=Math.max(alpha,0.4);}else panning={x:e.clientX-view.x,y:e.clientY-view.y};});
cv.addEventListener('pointermove',e=>{
  if(drag){moved=true;const p=toWorld(e);drag.x=p.x;drag.y=p.y;drag.vx=drag.vy=0;alpha=Math.max(alpha,0.3);}
  else if(panning){moved=true;view.x=e.clientX-panning.x;view.y=e.clientY-panning.y;}
  else{hover=pick(e);cv.style.cursor=hover?(hover.url?'pointer':'default'):'grab';
    if(hover){tip.hidden=false;tip.textContent=`${hover.label} · ${LABELS[hover.type]} · ${hover.deg} link${hover.deg===1?'':'s'}`;}else tip.hidden=true;}
  if(reduce)draw();});
cv.addEventListener('pointerup',e=>{if(drag&&!moved&&drag.url)location.href=drag.url;drag=null;panning=null;});
cv.addEventListener('pointerleave',()=>{hover=null;tip.hidden=true;});
cv.addEventListener('wheel',e=>{e.preventDefault();const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;
  const k=Math.min(4,Math.max(0.2,view.k*Math.exp(-e.deltaY*0.0015)));view.x=mx-(mx-view.x)*(k/view.k);view.y=my-(my-view.y)*(k/view.k);view.k=k;if(reduce)draw();},{passive:false});

document.querySelectorAll('[data-gtype]').forEach(cb=>cb.addEventListener('change',()=>{
  cb.checked?visibleTypes.add(cb.dataset.gtype):visibleTypes.delete(cb.dataset.gtype);alpha=Math.max(alpha,0.5);if(reduce)draw();}));
document.getElementById('graph-search').addEventListener('input',e=>{query=e.target.value.trim().toLowerCase();if(reduce)draw();});
document.getElementById('graph-reset').addEventListener('click',()=>{view={x:W/2,y:H/2,k:1,set:true};alpha=1;if(reduce)draw();});
addEventListener('resize',resize);resize();loop();
})();
"""


def render_graph_page(pages: list[dict], linkmap: dict, books: set[str], tag_index: dict, base: str) -> str:
    """Body HTML for /graph/: filters, a canvas, and the graph data embedded as JSON."""
    g = build_graph(pages, linkmap, books, tag_index, base)
    counts: dict[str, int] = {}
    for n in g["nodes"]:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    legend = "".join(
        f'<label class="inline-flex items-center gap-2 text-sm cursor-pointer"><input type="checkbox"{" checked" if k in GRAPH_DEFAULT_ON else ""} data-gtype="{k}">'
        f'<span class="inline-block w-3 h-3 rounded-full" style="background:{GRAPH_COLORS[k]}"></span>{GRAPH_LABELS[k]} ({counts.get(k, 0)})</label>'
        for k in GRAPH_COLORS if counts.get(k))
    data = json.dumps(g, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    js = GRAPH_JS.replace("@@COLORS@@", json.dumps(GRAPH_COLORS)).replace("@@LABELS@@", json.dumps(GRAPH_LABELS))
    return (
        '<h1 class="font-serif text-3xl font-black mb-2">Graph</h1>'
        f'<p class="text-stone-600 mb-4">{len(g["nodes"])} nodes, {len(g["links"])} connections. Hover to see what a note touches, drag nodes to rearrange, scroll to zoom, click to open.</p>'
        '<div class="flex flex-wrap items-center gap-x-5 gap-y-2 mb-4">'
        f'<input id="graph-search" type="search" placeholder="Find a node…" value="{GRAPH_DEFAULT_QUERY}" aria-label="Find a node" class="border border-stone-300 rounded-lg px-4 py-2 w-full md:w-64">'
        f'{legend}<button id="graph-reset" type="button" class="tag">Reset view</button></div>'
        '<div class="relative card !p-0 overflow-hidden"><canvas id="graph" class="w-full block touch-none cursor-grab" style="height:70vh;min-height:420px" '
        'role="img" aria-label="Interactive graph of connections between notes, verses, books and topics"></canvas>'
        '<div id="graph-tip" hidden class="absolute left-3 bottom-3 bg-white/95 border border-stone-200 rounded-lg px-3 py-1.5 text-sm shadow pointer-events-none"></div></div>'
        f'<noscript><p class="mt-4 text-stone-600">The graph needs JavaScript. Browse <a class="text-green-700" href="{base}/tags/">Topics</a> instead.</p></noscript>'
        f'<script id="graph-data" type="application/json">{data}</script><script>{js}</script>'
    )


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
    (out / "art").mkdir(parents=True)

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
        h = BASE_TMPL.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc[:160])).replace("@@BASE@@", base).replace("@@THEME_CSS@@", THEME_CSS).replace("@@BODY@@", body_html)
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

    def blurb_text(body: str, n: int) -> str:
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)  # [text](url) -> text
        t = re.sub(r"[#>*`\[\]]", "", t)
        return esc(re.sub(r"\s+", " ", t)[:n] + "…")

    def card_daily(p: dict) -> str:
        search = esc((p["title"] + " " + p.get("date", "") + " " + " ".join(p["fm"].get("tags", []))).lower())
        pills = tag_pills(p["fm"].get("tags", [])[:6])
        blurb = blurb_text(p["body"], 180)
        return (f'<article class="card" data-search="{search}"><p class="text-sm font-medium" style="color: var(--color-gold);">{esc(p.get("date",""))}</p>'
                f'<h3 class="font-display text-xl font-bold mt-1"><a class="hover:text-gold transition" href="{p["url"]}">{esc(p["title"])}</a></h3>'
                f'<p class="text-sm mt-2" style="color: #a8a29e;">{blurb}</p><div class="mt-3">{pills}</div></article>')

    def card_verse(p: dict) -> str:
        search = esc((p["title"] + " " + " ".join(p["fm"].get("tags", []))).lower())
        pills = tag_pills(p["fm"].get("tags", [])[:4])
        blurb = blurb_text(p["body"], 140)
        return (f'<article class="card" data-search="{search}"><h3 class="font-semibold"><a class="hover:text-gold transition" href="{p["url"]}">{esc(p["title"])}</a></h3>'
                f'<p class="text-sm mt-2" style="color: #a8a29e;">{blurb}</p><div class="mt-3">{pills}</div></article>')

    # ---- home
    stats = (f'<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
             f'<div class="card text-center"><p class="text-3xl font-bold" style="color: var(--color-gold);">{len(daily)}</p><p class="text-sm" style="color: #a8a29e;">Daily notes</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold" style="color: var(--color-gold);">{len(bible)}</p><p class="text-sm" style="color: #a8a29e;">Verse pages</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold" style="color: var(--color-gold);">{len(by_book)}</p><p class="text-sm" style="color: #a8a29e;">Books</p></div>'
             f'<div class="card text-center"><p class="text-3xl font-bold" style="color: var(--color-gold);">{len(tag_index)}</p><p class="text-sm" style="color: #a8a29e;">Topics</p></div></div>')
    hero = (f'<section class="rounded-2xl p-8 md:p-12 text-white mb-8" style="background:linear-gradient(135deg,var(--color-ink),var(--color-panel))">'
            f'<p class="mb-4 text-sm uppercase tracking-[0.3em]" style="color: var(--color-gold);">Faith · Strength · Brotherhood</p>'
            f'<h1 class="font-display text-5xl md:text-7xl">Man of God</h1>'
            f'<p class="mx-auto mt-6 max-w-2xl text-lg" style="color: #a8a29e;">Man of God, is a site that is a collection of daily readings with some thoughts on the verses, they are my thoughts and are not truth, The Word is truth and you should read for yourself, but maybe some thoughts could help, or draw you closer to reading the Bible for yourself. We would like to help men have a relationship with God and challenge each other to draw closer to God through His Word. We have added some resources and links to help build your faith and understanding.</p>'
            f'<div class="mt-8 flex flex-wrap justify-center gap-4"><a class="btn" href="{base}/accept-jesus/">Accept Jesus</a>'
            f'<a class="btn-sm py-2.5" href="{base}/daily/">Browse daily notes</a>'
            f'<a class="btn-sm py-2.5" href="{base}/bible/">Explore verse pages</a></div></section>'
            f'<blockquote class="card mb-8" style="border-left: 4px solid var(--color-gold);"><p class="font-display text-xl md:text-2xl" style="color: var(--color-gold);">“{esc(VERSE)}”</p></blockquote>'
            f'{stats}'
            f'<div class="flex items-center justify-between mt-10 mb-4"><h2 class="font-display text-2xl font-bold">Recent daily notes</h2><a class="text-gold font-medium hover:underline" href="{base}/daily/">View all →</a></div>'
            f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{"".join(card_daily(p) for p in daily[:6])}</div>'
            f'<div class="flex items-center justify-between mt-10 mb-4"><h2 class="font-display text-2xl font-bold">Recent verse pages</h2><a class="text-gold font-medium hover:underline" href="{base}/bible/">View all →</a></div>'
            f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">{"".join(card_verse(p) for p in bible[-8:][::-1])}</div>')
    write("", SITE_NAME, VERSE, hero)

    # ---- daily index + pages
    write("daily", "Daily notes", "Chronological daily Bible reading notes.",
          f'<h1 class="font-display text-3xl font-black mb-2">Daily notes</h1><p class="mb-6" style="color: #a8a29e;">Newest first. Open any note to read reflections, verse inserts, and harvested verse pages.</p>'
          f'<input id="filter" placeholder="Filter notes…" class="input mb-6">'
          f'<div class="grid gap-4 md:grid-cols-2">{"".join(card_daily(p) for p in daily)}</div>')
    for p in daily:
        html_body = render_blocks(p["body"], linkmap, base, {b for b in books})
        harvested = sorted({m.group(1).strip() for m in WIKILINK_RE.finditer(p["body"]) if " v " in m.group(1)})
        links = []
        for ref in harvested:
            u = linkmap.get(ref.lower()) or linkmap.get(slugify(ref))
            if u:
                links.append(f'<a class="tag" href="{u}">{esc(ref)}</a>')
        body_html = (f'<p class="text-sm font-medium" style="color: var(--color-gold);">{esc(p.get("date",""))}</p>'
                     f'<h1 class="font-display text-3xl md:text-4xl font-black mb-3">{esc(p["title"])}</h1>'
                     f'<div class="mb-6">{tag_pills(p["fm"].get("tags", []))}</div>'
                     f'<div class="prose-custom">{html_body}</div>'
                     + (f'<h2 class="font-display text-2xl font-bold mt-10 mb-3">Harvested verse pages</h2><div>{"".join(links)}</div>' if links else "")
                     + f'<p class="mt-10 text-sm"><a class="text-gold hover:underline" href="{base}/daily/">← All daily notes</a></p>')
        write(f"daily/{p['slug']}", p["title"], p["title"], body_html)

    # ---- bible index + pages
    books_sorted = sorted(by_book)
    opts = "".join(f'<button data-book="{esc(slugify(b))}" class="tag">{esc(b)} ({len(by_book[b])})</button>' for b in books_sorted)
    write("bible", "Verse pages", "Every harvested verse page, grouped by book.",
          f'<h1 class="font-display text-3xl font-black mb-2">Verse pages</h1><p class="mb-4" style="color: #a8a29e;">{len(bible)} pages across {len(books_sorted)} books.</p>'
          f'<input id="filter" placeholder="Filter passages…" class="input mb-4">'
          f'<div class="flex flex-wrap gap-2 mb-6"><button data-book="all" class="tag">All</button>{opts}</div>'
          f'<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">' + "".join(
              f'<div data-search="{esc((p["title"] + " " + " ".join(p["fm"].get("tags", []))).lower())}" data-book="{esc(slugify(p["book"]))}">{card_verse(p)}</div>'
              for p in bible) + '</div>'
          + '<script>document.querySelectorAll("[data-book]").forEach(b=>b.addEventListener("click",()=>{const f=b.dataset.book;document.querySelectorAll("#main [data-book].card, #main div[data-book]").forEach(()=>{});document.querySelectorAll(".grid [data-book]").forEach(c=>{c.style.display=(f==="all"||c.dataset.book===f)?"":"none";});}));</script>')
    for p in bible:
        html_body = render_blocks(p["body"], linkmap, base, books)
        related = [q for q in by_book.get(p["book"], []) if q["slug"] != p["slug"] and q["chapter"] == p["chapter"]][:8]
        aliases = "".join(f"<li>{esc(a)}</li>" for a in p["fm"].get("aliases", []))
        body_html = (f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/bible/">Verse pages</a> / <a class="text-gold hover:underline" href="{base}/books/{slugify(p["book"])}/">{esc(p["book"])}</a></p>'
                     f'<h1 class="font-display text-3xl md:text-4xl font-black mt-1 mb-3">{esc(p["title"])}</h1>'
                     f'<div class="mb-6">{tag_pills(p["fm"].get("tags", []))}</div>'
                     f'<div class="prose-custom">{html_body}</div>'
                     + (f'<div class="mt-6 p-4 card" style="border-left: 4px solid var(--color-gold);"><h3 class="font-semibold text-gold">Also known as</h3><ul class="list-disc ml-5" style="color: #a8a29e;">{aliases}</ul></div>' if aliases else "")
                     + ("".join(f'<h2 class="font-display text-2xl font-bold mt-10 mb-3">More in {esc(p["book"])} {esc(p["chapter"])}</h2><div class="grid gap-3 md:grid-cols-2 lg:grid-cols-3">' + "".join(card_verse(q) for q in related) + "</div>" if related else "")))
        write(f"bible/{p['slug']}", p["title"], p["title"], body_html)

    # ---- books
    write("books", "Books", "Verse pages grouped by Bible book.",
          '<h1 class="font-display text-3xl font-black mb-2">Books</h1><p class="mb-6" style="color: #a8a29e;">Verse pages grouped by Bible book.</p><div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">'
          + "".join(f'<a class="card" href="{base}/books/{slugify(b)}/"><h3 class="font-bold">{esc(b.title()) if b.islower() else esc(b)}</h3><p class="text-sm" style="color: #a8a29e;">{len(by_book[b])} passages</p></a>' for b in books_sorted) + "</div>")
    for b in books_sorted:
        groups: dict[str, list[dict]] = {}
        for p in by_book[b]:
            groups.setdefault(p["chapter"] or "—", []).append(p)
        secs = ""
        for ch in sorted(groups, key=lambda c: int(c) if c.isdigit() else 999):
            items = "".join(f'<a class="card block" href="{q["url"]}"><strong>{esc(q["title"])}</strong><br><span class="text-sm" style="color: #a8a29e;">{" ".join(q["fm"].get("tags", [])[:4])}</span></a>' for q in groups[ch])
            secs += f'<section class="card mb-6"><h2 class="font-bold text-lg mb-3">{esc(b)} {esc(ch)}</h2><div class="grid gap-3 md:grid-cols-2">{items}</div></section>'
        write(f"books/{slugify(b)}", b, f"Verse pages in {b}", f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/books/">Books</a> / {esc(b)}</p><h1 class="font-display text-3xl font-black mt-1 mb-4">{esc(b)}</h1>{secs}')

    # ---- tags
    write("tags", "Topics", "Browse by theme.",
          '<h1 class="font-display text-3xl font-black mb-2">Topics</h1><p class="mb-6" style="color: #a8a29e;">Themes from passages and reflections.</p><div class="flex flex-wrap gap-2">'
          + "".join(f'<a class="tag" href="{base}/tags/{slugify(t)}/">#{esc(t)} ({len(tag_index[t])})</a>' for t in sorted(tag_index)) + "</div>")
    for t, plist in tag_index.items():
        cards = "".join(card_daily(p) if p["kind"] == "daily" else card_verse(p) for p in plist)
        write(f"tags/{slugify(t)}", f"#{t}", f"Pages tagged {t}",
              f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/tags/">Topics</a> / #{esc(t)}</p><h1 class="font-display text-3xl font-black mt-1 mb-4">#{esc(t)}</h1><div class="grid gap-4 md:grid-cols-2">{cards}</div>')

    # ---- shop (placeholder until the store opens)
    write("shop", "Shop", "The Man of God shop is coming soon.",
          '<div class="text-center py-16"><h1 class="font-display text-5xl font-black" style="color: var(--color-gold);">Coming Soon</h1>'
          '<p class="mt-4" style="color: #a8a29e;">The Man of God shop is on its way. Check back soon.</p>'
          f'<p class="mt-6"><a class="text-gold font-semibold hover:underline" href="{base}/">← Home</a></p></div>')

    # ---- graph (Obsidian-style relationship view)
    write("graph", "Graph", "Interactive map of how daily notes, verses, books and topics connect.",
          render_graph_page(pages, linkmap, books, tag_index, base))

    # ---- art gallery
    art_projects = []
    if ART_DIR.exists():
        for folder in sorted(ART_DIR.iterdir()):
            if folder.is_dir() and folder.name != "__pycache__":
                slug = slugify(folder.name)
                readme = folder / "README.md"
                export_dir = folder / "exports"
                
                # Load metadata from README
                notes = ""
                if readme.exists():
                    content = readme.read_text(encoding="utf-8", errors="replace")
                    lines = content.split("\n")
                    if lines and lines[0].startswith("#"):
                        notes = "\n".join(lines[1:]).strip()
                    else:
                        notes = content.strip()
                
                # Find exported images
                images = []
                if export_dir.exists():
                    for img in sorted(export_dir.glob("*.png")) + sorted(export_dir.glob("*.jpg")) + sorted(export_dir.glob("*.jpeg")):
                        if not img.stem.endswith("_watermarked"):
                            images.append(img.name)
                
                if images:
                    # Content-hash query string so a changed export busts the browser/CDN cache
                    urls = {
                        img: f"{base}/art/{slug}/{img}?v={hashlib.md5((export_dir / img).read_bytes()).hexdigest()[:8]}"
                        for img in images
                    }
                    project = {"slug": slug, "title": folder.name, "images": images, "urls": urls, "notes": notes}
                    art_projects.append(project)
                    
                    # Copy images to dist
                    proj_out = out / "art" / slug
                    proj_out.mkdir(parents=True, exist_ok=True)
                    for img in images:
                        src = export_dir / img
                        dst = proj_out / img
                        shutil.copy2(src, dst)
                    
                    # Generate project page
                    gallery_html = '<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">'
                    for idx, img in enumerate(images):
                        gallery_html += f'<a href="#" data-lightbox="{urls[img]}" class="card !p-0 overflow-hidden group"><img src="{urls[img]}" alt="Image {idx+1}" class="w-full h-48 object-cover group-hover:opacity-90 transition" style="user-select: none;" data-no-save /></a>'
                    gallery_html += '</div>'
                    
                    # Convert markdown notes to HTML
                    notes_html = ""
                    if notes:
                        notes_rendered = render_blocks(notes, linkmap, base, books)
                        notes_html = f'<div class="prose-custom mb-8">{notes_rendered}</div>'
                    
                    write(f"art/{slug}", folder.name, f"Art project: {folder.name}",
                          f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/art/">Art</a> / {esc(folder.name)}</p><h1 class="font-display text-3xl font-black mt-1 mb-6">{esc(folder.name)}</h1>{notes_html}{gallery_html}')
    
    # Art gallery index
    if art_projects:
        cards_html = '<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">'
        for proj in art_projects:
            first_img = proj["images"][0]
            cards_html += f'<a href="{base}/art/{proj["slug"]}/" class="card !p-0 overflow-hidden group"><div class="relative w-full h-48 bg-panel rounded mb-3 overflow-hidden"><img src="{proj["urls"][first_img]}" alt="{proj["title"]}" class="w-full h-full object-cover group-hover:scale-105 transition" style="user-select: none;" data-no-save /></div><div class="p-4"><h3 class="font-bold text-lg">{esc(proj["title"])}</h3><p class="text-sm" style="color: #a8a29e;">{len(proj["images"])} image{"s" if len(proj["images"]) != 1 else ""}</p></div></a>'
        cards_html += '</div>'
        gallery_index = f'<h1 class="font-display text-3xl font-black mb-2">Art & Investigations</h1><p class="mb-6" style="color: #a8a29e;">Creative explorations, design studies, and artistic investigations. Images are watermarked to prevent AI training use.</p>{cards_html}'
    else:
        gallery_index = '<h1 class="font-display text-3xl font-black mb-2">Art & Investigations</h1><p style="color: #a8a29e;">No art projects yet. Add folders to the Art/ directory to get started.</p>'
    
    write("art", "Art & Investigations", "Art projects, explorations, and investigations",
          gallery_index)

    # ---- resources (books, podcasts, YouTube channels)
    def qa(t: str) -> str:
        return html.escape(t, quote=True)

    resources = []
    if RESOURCE_DIR.exists():
        for f in sorted(RESOURCE_DIR.glob("*.md")):
            if f.name.startswith("_") or f.name.lower() == "readme.md":
                continue
            r = parse_resource(f)
            if r:
                resources.append(r)
    resources.sort(key=lambda r: (list(RESOURCE_TYPES).index(r["type"]), r["title"].lower()))

    img_out = out / "resources" / "images"
    for r in resources:
        r["img_url"] = ""
        if r["image"]:
            img_out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(r["image"], img_out / r["image"].name)
            # content hash busts the browser/CDN cache when the image is replaced
            r["img_url"] = f"{base}/resources/images/{quote(r['image'].name)}?v={hashlib.md5(r['image'].read_bytes()).hexdigest()[:8]}"

    def res_image(r: dict, cls: str) -> str:
        if r["img_url"]:
            return f'<img src="{r["img_url"]}" alt="{qa(r["title"])}" class="{cls}" style="margin: 0; box-shadow: none;" loading="lazy">'
        return f'<div class="{cls} h-48 flex items-center justify-center text-sm" style="color: #78716c;">{esc(RESOURCE_TYPES[r["type"]])}</div>'

    def res_links(r: dict) -> str:
        return "".join(f'<a class="btn-sm" href="{qa(u)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a> ' for label, u in r["links"])

    def res_card(r: dict) -> str:
        search = qa((r["title"] + " " + r["by"] + " " + RESOURCE_TYPES[r["type"]] + " " + " ".join(r["tags"]) + " " + r["body"][:400]).lower())
        by = f'<p class="text-sm" style="color: #a8a29e;">{esc(r["by"])}</p>' if r["by"] else ""
        return (f'<article class="card flex flex-col" data-rtype="{r["type"]}" data-search="{search}">'
                f'<a href="{base}/resources/{r["slug"]}/">{res_image(r, "w-full h-48 object-contain rounded mb-3 bg-ink")}</a>'
                f'<p class="text-xs uppercase tracking-wide" style="color: var(--color-gold);">{esc(RESOURCE_TYPES[r["type"]])}</p>'
                f'<h3 class="font-display text-xl font-bold"><a class="hover:text-gold transition" href="{base}/resources/{r["slug"]}/">{esc(r["title"])}</a></h3>{by}'
                f'<p class="text-sm mt-2 flex-1" style="color: #a8a29e;">{blurb_text(r["body"], 160)}</p>'
                f'<div class="mt-3">{res_links(r)}</div></article>')

    if resources:
        used = [t for t in RESOURCE_TYPES if any(r["type"] == t for r in resources)]
        buttons = '<button data-rfilter="all" class="tag">All</button>' + "".join(
            f'<button data-rfilter="{t}" class="tag">{esc(RESOURCE_TYPES[t])} ({sum(r["type"] == t for r in resources)})</button>' for t in used)
        res_body = ('<input id="res-filter" placeholder="Search resources…" class="input mb-4">'
                    f'<div class="flex flex-wrap gap-2 mb-6">{buttons}</div>'
                    '<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">' + "".join(res_card(r) for r in resources) + '</div>'
                    '<script>(function(){var q=document.getElementById("res-filter"),t="all";'
                    'function a(){var s=q.value.toLowerCase();document.querySelectorAll("[data-rtype]").forEach(function(c){'
                    'c.style.display=((t==="all"||c.dataset.rtype===t)&&c.dataset.search.indexOf(s)>-1)?"":"none"})}'
                    'q.addEventListener("input",a);document.querySelectorAll("[data-rfilter]").forEach(function(b){'
                    'b.addEventListener("click",function(){t=b.dataset.rfilter;a()})})})();</script>')
    else:
        res_body = '<p style="color: #a8a29e;">No recommendations yet. Add a markdown file to the Resources/ folder to get started.</p>'
    # Scripture images: Resources/Scripture-Images/*.png|jpg, shown as a lightbox gallery
    scripture_imgs = []
    if SCRIPTURE_IMG_DIR.exists():
        for img in sorted(p for p in SCRIPTURE_IMG_DIR.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")):
            fname = slugify(img.stem) + img.suffix.lower()
            si_out = out / "resources" / "scripture-images"
            si_out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, si_out / fname)
            url = f"{base}/resources/scripture-images/{fname}?v={hashlib.md5(img.read_bytes()).hexdigest()[:8]}"
            scripture_imgs.append((img.stem, url))
    scripture_link = ""
    if scripture_imgs:
        grid = "".join(
            f'<figure><a href="#" data-lightbox="{url}" class="card !p-0 overflow-hidden block"><img src="{url}" alt="{qa(title)}" class="w-full h-48 object-cover hover:opacity-90 transition" loading="lazy"></a>'
            f'<figcaption class="text-sm mt-2" style="color: #a8a29e;">{esc(title)}</figcaption></figure>'
            for title, url in scripture_imgs)
        write("resources/scripture-images", "Scripture Images", "Scripture images to view and share.",
              f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/resources/">Resources</a> / Scripture Images</p>'
              f'<h1 class="font-display text-3xl font-black mt-1 mb-6">Scripture Images</h1>'
              f'<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{grid}</div>')
        scripture_link = (f'<p class="mb-6"><a class="btn-sm" href="{base}/resources/scripture-images/">'
                          f'Scripture Images ({len(scripture_imgs)})</a></p>')
    write("resources", "Resources", "Books, podcasts, YouTube channels and scripture images worth your time.",
          '<h1 class="font-display text-3xl font-black mb-2">Resources</h1>'
          '<p class="mb-6" style="color: #a8a29e;">Books, podcasts and YouTube channels worth your time. Links go to external sites.</p>'
          + scripture_link + res_body)

    for r in resources:
        by = f'<p style="color: #a8a29e;">{esc(r["by"])}</p>' if r["by"] else ""
        write(f"resources/{r['slug']}", r["title"], f"{r['title']} — {r['by']}" if r["by"] else r["title"],
              f'<p class="text-sm"><a class="text-gold hover:underline" href="{base}/resources/">Resources</a> / {esc(RESOURCE_TYPES[r["type"]])}</p>'
              f'<div class="grid gap-8 md:grid-cols-3 mt-3"><div>{res_image(r, "w-full rounded bg-panel")}</div>'
              f'<div class="md:col-span-2"><h1 class="font-display text-3xl md:text-4xl font-black mb-1">{esc(r["title"])}</h1>{by}'
              f'<div class="my-4">{res_links(r)}</div>'
              f'<div class="prose-custom">{render_blocks(r["body"], linkmap, base, books)}</div>'
              f'<div class="mt-4">{"".join(f"<span class=tag>#{esc(t)}</span>" for t in r["tags"])}</div></div></div>')

    # ---- standalone pages: Pages/<slug>.md (frontmatter: title, description) -> /<slug>/
    if PAGES_DIR.exists():
        for f in sorted(PAGES_DIR.glob("*.md")):
            if f.name.startswith("_"):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            parts = text.split("---", 2)
            if not text.startswith("---") or len(parts) < 3:
                print(f"  ⚠ {f.name}: no frontmatter, skipped")
                continue
            fm = {k.strip().lower(): v.strip().strip('"').strip("'")
                  for k, _, v in (ln.partition(":") for ln in parts[1].splitlines() if ":" in ln)}
            title = fm.get("title") or f.stem
            write(slugify(f.stem), title, fm.get("description", title),
                  f'<h1 class="font-display text-3xl md:text-4xl font-black mb-6">{esc(title)}</h1>'
                  f'<div class="prose-custom">{render_blocks(parts[2].lstrip(chr(10)).replace("@@BASE@@", base), linkmap, base, books)}</div>')

    # Copy exported logos to dist
    logo_dir = REPO / "logo"
    logo_exports = logo_dir / "exports"
    if logo_exports.exists():
        logos_out = out / "logos"
        logos_out.mkdir(parents=True, exist_ok=True)
        for logo_file in logo_exports.glob("*.png"):
            shutil.copy2(logo_file, logos_out / logo_file.name)

    # ---- misc
    (out / "404.html").write_text(render_page("Not found", "Page not found",
        '<div class="text-center py-16"><h1 class="font-display text-5xl font-black" style="color: var(--color-gold);">404</h1><p class="mt-2" style="color: #a8a29e;">That page is not in this vault.</p><p class="mt-6"><a class="text-gold font-semibold hover:underline" href="' + base + '/">← Home</a></p></div>'), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
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
