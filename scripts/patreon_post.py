#!/usr/bin/env python3
"""Turn a Daily note into the pieces of a manual Patreon post.

The Patreon API v2 is read-only, so posts are created in the browser. This
script prepares everything the browser step needs:

  * title        - the part of the note name in brackets, e.g. "Big Picture Hope"
  * date         - the note's own date (used as the publish date)
  * tags         - the note's frontmatter tags (the same ones the site uses)
  * site_url     - the published vault page for the note
  * body (html)  - intro, then per reading: a linked heading, the quoted
                   verses and the commentary, with Obsidian syntax removed

Usage:
  patreon_post.py "Daily/2026-10-19 (Big Picture Hope).md" --out DIR [--copy]

Writes DIR/post.json and DIR/post.html. With --copy the HTML is also placed on
the macOS clipboard as rich text, ready to paste into the Patreon editor.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

SITE = "https://manofgod.online/vault"
SKIP_FROM = "## Harvested verse pages"


def slugify(name: str) -> str:
    """Mirror scripts/build-site.py so the link matches the published page."""
    s = name.strip().lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def split_frontmatter(text: str):
    """Return (tags, body) from a note whose frontmatter starts on line 1."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return [], text
    tags = re.findall(r"^\s*-\s*(\S+)\s*$", m.group(1), re.M)
    return tags, text[m.end():]


def inline(line: str) -> str:
    """Obsidian/markdown inline syntax -> HTML."""
    line = re.sub(r"%%.*?%%", "", line)
    line = re.sub(r"\[\[(\d+)\]\]\(", r"[\1](", line)      # Logos footnote [[1]](url)
    line = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", line)
    line = re.sub(r"\[\[([^\]]*)\]\]", r"\1", line)
    out, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)\s]+)\)", line):
        out.append(html.escape(line[pos:m.start()]))
        link = f'<a href="{html.escape(m.group(2))}">{html.escape(m.group(1))}</a>'
        out.append(f"<sup>{link}</sup>" if m.group(1).isdigit() else link)
        pos = m.end()
    out.append(html.escape(line[pos:]))
    text = "".join(out)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![\w*])_(.+?)_(?![\w*])", r"<em>\1</em>", text)


def paragraphs(lines):
    """Group consecutive non-blank lines into <p> blocks (line breaks kept).

    A markdown heading line (``#### Daily Prayer``) ends the current block and
    becomes its own <h4>, so it never shows up as literal ``####`` text.
    """
    blocks, cur = [], []
    for ln in lines + [""]:
        heading = re.fullmatch(r"#{1,6}\s+(.+)", ln.strip())
        if heading:
            if cur:
                blocks.append("<p>" + "<br>".join(inline(c) for c in cur) + "</p>")
                cur = []
            blocks.append(f"<h4>{inline(heading.group(1))}</h4>")
        elif ln.strip():
            cur.append(ln.strip())
        elif cur:
            blocks.append("<p>" + "<br>".join(inline(c) for c in cur) + "</p>")
            cur = []
    return blocks


def build_body(body: str) -> str:
    """Intro + one section per [!bible] callout, minus the verse dump."""
    body = body.split(SKIP_FROM)[0]
    parts = [[]]            # parts[0] is the intro, then one list per reading
    headings = [None]
    in_callout = False
    for ln in body.splitlines():
        m = re.match(r">\s*\[!bible\][+-]?\s*\[([^\]]+)\]\(([^)\s]+)\)", ln)
        if m:
            headings.append(m.groups())
            parts.append([])
            in_callout = True
            continue
        if in_callout:
            if "%%>" in ln:
                in_callout = False
            continue
        if re.fullmatch(r"\s*(\[\[[^\]]+\]\]\s*)+", ln):   # backlink line
            continue
        if re.fullmatch(r"\s*(\[[^\]]+\]\([^)]+\)\s*\*?\s*)+", ln) and not headings[-1]:
            continue                                         # plain reading-links line
        parts[-1].append(ln)

    out = paragraphs(parts[0])
    for head, lines in zip(headings[1:], parts[1:]):
        title, url = head
        label = re.sub(r"\s*-\s*[\w-]+$", "", title)         # drop " - WEB-OFFLINE"
        out.append(f'<h3><a href="{html.escape(url)}">{html.escape(label)}</a></h3>')
        out.extend(paragraphs(lines))
    return "\n".join(out)


def copy_html(doc: str):
    """Put HTML on the macOS clipboard as rich text."""
    script = f'set the clipboard to «data HTML{doc.encode().hex()}»'
    subprocess.run(["osascript", "-e", script], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("note")
    ap.add_argument("--out", required=True, help="directory for post.json / post.html")
    ap.add_argument("--copy", action="store_true", help="copy the HTML to the clipboard")
    args = ap.parse_args()

    note = Path(args.note)
    stem = note.stem
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s*\((.*?)\)?$", stem)
    if not m:
        sys.exit(f"Can't read date/title from note name: {stem}")
    date, title = m.groups()
    title = title.strip()

    tags, body = split_frontmatter(note.read_text(encoding="utf-8"))
    site_url = f"{SITE}/daily/{slugify(stem)}/"
    post_html = build_body(body)
    post_html += f'\n<p>Read it on the site: <a href="{site_url}">{site_url}</a></p>'

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    preview_html = f"<h1>{html.escape(title)}</h1>\n{post_html}"
    if tags:
        preview_html += f"\n<p><strong>Tags:</strong> {html.escape(', '.join(tags))}</p>"
    (out / "post.html").write_text(preview_html, encoding="utf-8")
    (out / "post.json").write_text(json.dumps(
        {"title": title, "date": date, "tags": tags, "site_url": site_url}, indent=2),
        encoding="utf-8")
    if args.copy:
        copy_html(post_html)
    print(json.dumps({"title": title, "date": date, "tags": tags, "site_url": site_url}))


if __name__ == "__main__":
    main()
