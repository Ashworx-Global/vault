#!/usr/bin/env python3
"""Harvest Bible passages from a vault note into linked Bible/ verse pages.

Reads a daily/study note containing:
  - Bible Verse plugin callouts:  > [!bible]- [Book C:V-R - ESV](url)
    with per-verse lines:          > [[Book C#^V|V]]. verse text
  - Logos links:                   [ref or snippet](https://ref.ly/...)
  - Short refs on their own line:  Zec 7:5   /   Ac 23:21-22

For every distinct passage found it creates VAULT/Bible/<Book> <C> v <R>.md
with properties (lowercase tags, resolvable alias, cssclasses: verse),
the verse text harvested from the note (or an ESV-paste placeholder),
backlinks to the source note, and parent/child cross-links between block
pages and focused-verse pages inside them.

Existing pages are NEVER overwritten (reported as skipped).

Usage:
    python3 harvest_verses.py "/path/to/vault/Daily/2026-09-25 (...).md"
    python3 harvest_verses.py --dry-run <note>   # print plan only
    python3 harvest_verses.py --vault /path/to/vault <note>

After running, the agent refines each new page theologically (theme tags,
Thematic Alias) following vault conventions.
"""

import re
import sys
from pathlib import Path

EN_DASH = "\u2013"

# abbreviation -> (Display Name, slug)
BOOKS = {
    "genesis": ("Genesis", "genesis"), "gen": ("Genesis", "genesis"),
    "exodus": ("Exodus", "exodus"), "ex": ("Exodus", "exodus"), "exo": ("Exodus", "exodus"),
    "leviticus": ("Leviticus", "leviticus"), "lev": ("Leviticus", "leviticus"),
    "numbers": ("Numbers", "numbers"), "num": ("Numbers", "numbers"),
    "deuteronomy": ("Deuteronomy", "deuteronomy"), "deut": ("Deuteronomy", "deuteronomy"), "dt": ("Deuteronomy", "deuteronomy"),
    "joshua": ("Joshua", "joshua"), "josh": ("Joshua", "joshua"),
    "judges": ("Judges", "judges"), "judg": ("Judges", "judges"),
    "ruth": ("Ruth", "ruth"), "ru": ("Ruth", "ruth"),
    "1samuel": ("1 Samuel", "1samuel"), "1sa": ("1 Samuel", "1samuel"),
    "2samuel": ("2 Samuel", "2samuel"), "2sa": ("2 Samuel", "2samuel"),
    "1kings": ("1 Kings", "1kings"), "1ki": ("1 Kings", "1kings"),
    "2kings": ("2 Kings", "2kings"), "2ki": ("2 Kings", "2kings"),
    "1chronicles": ("1 Chronicles", "1chronicles"), "1ch": ("1 Chronicles", "1chronicles"), "1chr": ("1 Chronicles", "1chronicles"),
    "2chronicles": ("2 Chronicles", "2chronicles"), "2ch": ("2 Chronicles", "2chronicles"), "2chr": ("2 Chronicles", "2chronicles"),
    "ezra": ("Ezra", "ezra"), "ezr": ("Ezra", "ezra"),
    "nehemiah": ("Nehemiah", "nehemiah"), "neh": ("Nehemiah", "nehemiah"),
    "esther": ("Esther", "esther"), "esth": ("Esther", "esther"),
    "job": ("Job", "job"),
    "psalms": ("Psalm", "psalm"), "psalm": ("Psalm", "psalm"), "ps": ("Psalm", "psalm"), "psa": ("Psalm", "psalm"),
    "proverbs": ("Proverbs", "proverbs"), "prov": ("Proverbs", "proverbs"),
    "ecclesiastes": ("Ecclesiastes", "ecclesiastes"), "eccl": ("Ecclesiastes", "ecclesiastes"),
    "songofsolomon": ("Song of Solomon", "song"), "song": ("Song of Solomon", "song"),
    "isaiah": ("Isaiah", "isaiah"), "isa": ("Isaiah", "isaiah"), "is": ("Isaiah", "isaiah"),
    "jeremiah": ("Jeremiah", "jeremiah"), "jer": ("Jeremiah", "jeremiah"),
    "lamentations": ("Lamentations", "lamentations"), "lam": ("Lamentations", "lamentations"),
    "ezekiel": ("Ezekiel", "ezekiel"), "eze": ("Ezekiel", "ezekiel"), "ezek": ("Ezekiel", "ezekiel"),
    "daniel": ("Daniel", "daniel"), "dan": ("Daniel", "daniel"),
    "hosea": ("Hosea", "hosea"), "hos": ("Hosea", "hosea"),
    "joel": ("Joel", "joel"),
    "amos": ("Amos", "amos"), "amo": ("Amos", "amos"),
    "obadiah": ("Obadiah", "obadiah"), "oba": ("Obadiah", "obadiah"),
    "jonah": ("Jonah", "jonah"), "jon": ("Jonah", "jonah"),
    "micah": ("Micah", "micah"), "mic": ("Micah", "micah"),
    "nahum": ("Nahum", "nahum"), "nah": ("Nahum", "nahum"),
    "habakkuk": ("Habakkuk", "habakkuk"), "hab": ("Habakkuk", "habakkuk"),
    "zephaniah": ("Zephaniah", "zephaniah"), "zep": ("Zephaniah", "zephaniah"),
    "haggai": ("Haggai", "haggai"), "hag": ("Haggai", "haggai"),
    "zechariah": ("Zechariah", "zechariah"), "zec": ("Zechariah", "zechariah"), "zech": ("Zechariah", "zechariah"),
    "malachi": ("Malachi", "malachi"), "mal": ("Malachi", "malachi"),
    "matthew": ("Matthew", "matthew"), "matt": ("Matthew", "matthew"), "mt": ("Matthew", "matthew"),
    "mark": ("Mark", "mark"), "mk": ("Mark", "mark"),
    "luke": ("Luke", "luke"), "lk": ("Luke", "luke"),
    "john": ("John", "john"), "jn": ("John", "john"),
    "acts": ("Acts", "acts"), "ac": ("Acts", "acts"),
    "romans": ("Romans", "romans"), "rom": ("Romans", "romans"), "ro": ("Romans", "romans"),
    "1corinthians": ("1 Corinthians", "1corinthians"), "1co": ("1 Corinthians", "1corinthians"),
    "2corinthians": ("2 Corinthians", "2corinthians"), "2co": ("2 Corinthians", "2corinthians"),
    "galatians": ("Galatians", "galatians"), "gal": ("Galatians", "galatians"),
    "ephesians": ("Ephesians", "ephesians"), "eph": ("Ephesians", "ephesians"),
    "philippians": ("Philippians", "philippians"), "phil": ("Philippians", "philippians"), "php": ("Philippians", "philippians"),
    "colossians": ("Colossians", "colossians"), "col": ("Colossians", "colossians"),
    "1thessalonians": ("1 Thessalonians", "1thessalonians"), "1th": ("1 Thessalonians", "1thessalonians"),
    "2thessalonians": ("2 Thessalonians", "2thessalonians"), "2th": ("2 Thessalonians", "2thessalonians"),
    "1timothy": ("1 Timothy", "1timothy"), "1ti": ("1 Timothy", "1timothy"),
    "2timothy": ("2 Timothy", "2timothy"), "2ti": ("2 Timothy", "2timothy"),
    "titus": ("Titus", "titus"), "tit": ("Titus", "titus"),
    "philemon": ("Philemon", "philemon"), "phm": ("Philemon", "philemon"),
    "hebrews": ("Hebrews", "hebrews"), "heb": ("Hebrews", "hebrews"),
    "james": ("James", "james"), "jas": ("James", "james"),
    "1peter": ("1 Peter", "1peter"), "1pe": ("1 Peter", "1peter"),
    "2peter": ("2 Peter", "2peter"), "2pe": ("2 Peter", "2peter"),
    "1john": ("1 John", "1john"), "1jn": ("1 John", "1john"),
    "2john": ("2 John", "2john"), "2jn": ("2 John", "2john"),
    "3john": ("3 John", "3john"), "3jn": ("3 John", "3john"),
    "jude": ("Jude", "jude"),
    "revelation": ("Revelation", "revelation"), "rev": ("Revelation", "revelation"),
}


def norm_book(s):
    key = re.sub(r"\s+", "", s).lower()
    return BOOKS.get(key)


REF_RE = re.compile(
    r"^\s*(\d?\s?[A-Za-z]+)\s+(\d+)\s*:\s*(\d+)"
    r"(?:\s*[-\u2013\u2014]\s*(\d+)?(?::(\d+))?)?\s*\.?\s*$"
)


def parse_ref(s):
    """'Zechariah 6:1-7:14' -> (display, slug, c1, v1, c2, v2). None if no match."""
    m = REF_RE.match(s.strip())
    if not m:
        return None
    book = norm_book(m.group(1))
    if not book:
        return None
    display, slug = book
    c1, v1 = int(m.group(2)), int(m.group(3))
    if m.group(4) is None:
        return (display, slug, c1, v1, c1, v1)
    if m.group(5) is None:
        # same-chapter range: "Job 29:13-25"
        return (display, slug, c1, v1, c1, int(m.group(4)))
    # cross-chapter range: "Acts 22:22-23:22"
    return (display, slug, c1, v1, int(m.group(4)), int(m.group(5)))


def page_name(display, c, v1, v2):
    if v1 == v2:
        return f"{display} {c} v {v1}"
    return f"{display} {c} v {v1}{EN_DASH}{v2}"


def clean_text(t):
    return re.sub(r"\s+", " ", t).strip()


def find_vault(note_path):
    p = Path(note_path).resolve()
    for parent in [p.parent] + list(p.parents):
        if (parent / ".obsidian").is_dir():
            return parent
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    vault_arg = None
    if "--vault" in sys.argv:
        vault_arg = sys.argv[sys.argv.index("--vault") + 1]
    if not args:
        print("usage: harvest_verses.py [--dry-run] [--vault PATH] <note.md>")
        sys.exit(2)

    note = Path(args[0])
    text = note.read_text(encoding="utf-8")
    lines = text.splitlines()
    vault = Path(vault_arg) if vault_arg else find_vault(note)
    if vault is None:
        print("ERROR: vault not found (no .obsidian ancestor). Use --vault.")
        sys.exit(1)
    bible_dir = vault / "Bible"
    note_title = note.stem

    # 1. verse texts from [[Book C#^V|V]] lines
    verses = {}  # (display, chapter, verse) -> text
    verse_line_re = re.compile(r"^>\s*\[\[([^\]]+?)#\^(\d+)\|\d+\]\]\.?\s?(.*)$")
    for ln in lines:
        m = verse_line_re.match(ln)
        if not m:
            continue
        chap_part, vnum, vtext = m.group(1).strip(), int(m.group(2)), clean_text(m.group(3))
        cm = re.match(r"^(.*?)\s*(\d+)\s*$", chap_part)
        if not cm:
            continue
        book = norm_book(cm.group(1))
        if not book or not vtext:
            continue
        verses[(book[0], int(cm.group(2)), vnum)] = vtext

    # 2. passages: bible-callout headers, split per chapter using verses present
    header_re = re.compile(r"^>\s*\[!bible\][+-]?\s*\[(.+?)\s*-\s*ESV\]")
    blocks = []  # (display, slug, chapter, [sorted verses])
    for ln in lines:
        m = header_re.match(ln)
        if not m:
            continue
        ref = parse_ref(m.group(1))
        if not ref:
            print(f"WARN: could not parse header ref: {m.group(1)!r}")
            continue
        display, slug, c1, v1, c2, v2 = ref
        for ch in range(c1, c2 + 1):
            vs = sorted(v for (b, c, v) in verses if b == display and c == ch)
            if vs:
                blocks.append((display, slug, ch, vs))

    # 3. focused refs: own-line short refs + ref-like markdown link texts
    focused = []  # (display, slug, c1, v1, c2, v2, origin)
    seen = set()
    link_re = re.compile(r"\[([^\]]+)\]\((https?://[^)]*|)\)")

    def add_focus(display, slug, c1, v1, c2, v2, origin):
        key = (display, c1, v1, c2, v2)
        if key not in seen:
            seen.add(key)
            focused.append((display, slug, c1, v1, c2, v2, origin))

    for ln in lines:
        stripped = ln.strip().lstrip(">").strip()
        ref = parse_ref(stripped)
        if ref:
            add_focus(*ref, "explicit")
            continue
        for lm in link_re.finditer(ln):
            ref = parse_ref(lm.group(1))
            if ref:
                add_focus(*ref, "link")

    # drop focused refs fully covered by nothing... keep all (user wants both)
    # 4. build pages
    pages = {}  # name -> dict(display, slug, ch, v1, v2, kind)

    def add_page(display, slug, ch, v1, v2, kind):
        name = page_name(display, ch, v1, v2)
        if name not in pages:
            pages[name] = dict(display=display, slug=slug, ch=ch,
                               v1=v1, v2=v2, kind=kind)

    for display, slug, ch, vs in blocks:
        add_page(display, slug, ch, vs[0], vs[-1], "block")
    for display, slug, c1, v1, c2, v2, origin in focused:
        if c1 == c2:
            add_page(display, slug, c1, v1, v2, "focus")
        else:
            for ch in range(c1, c2 + 1):
                lo = v1 if ch == c1 else 1
                hi = v2 if ch == c2 else 999
                vs = sorted(v for (b, c, v) in verses
                            if b == display and c == ch and lo <= v <= hi)
                if vs:
                    add_page(display, slug, ch, vs[0], vs[-1],
                             "focus" if origin == "explicit" else "split")
                else:
                    add_page(display, slug, ch, lo if lo != 999 else 1,
                             lo if lo != 999 else 1,
                             "focus" if origin == "explicit" else "split")

    # drop header/link-derived *split ranges* fully inside a block page.
    # Explicit short-ref pages are always kept (user's studied focus),
    # as are single verses (block + focused, cross-linked).
    block_spans = {(p["display"], p["ch"], p["v1"], p["v2"])
                   for p in pages.values() if p["kind"] == "block"}
    pages = {n: p for n, p in pages.items()
             if not (p["kind"] == "split" and any(
                 b == p["display"] and c == p["ch"] and lo <= p["v1"] and p["v2"] <= hi
                 for b, c, lo, hi in block_spans))}
    # parent/child links: focus inside a block range of same book+chapter
    children_of = {n: [] for n, p in pages.items() if p["kind"] == "block"}
    parent_of = {}
    for n, p in pages.items():
        if p["kind"] != "focus":
            continue
        for bn, b in pages.items():
            if b["kind"] == "block" and b["display"] == p["display"] \
                    and b["ch"] == p["ch"] and b["v1"] <= p["v1"] and p["v2"] <= b["v2"] \
                    and bn != n:
                parent_of.setdefault(n, []).append(bn)
                children_of[bn].append(n)

    created, skipped = [], []
    for name in sorted(pages):
        p = pages[name]
        dest = bible_dir / f"{name}.md"
        if dest.exists():
            skipped.append(name)
            continue
        vtexts = [(v, verses.get((p["display"], p["ch"], v)))
                  for v in range(p["v1"], p["v2"] + 1)]
        missing = [v for v, t in vtexts if not t]
        if missing and len(vtexts) > 3:
            # long page with gaps: keep present verses only
            vtexts = [(v, t) for v, t in vtexts if t]
        if dry:
            created.append(name + "  (dry-run)")
            continue
        body_verses = []
        for v, t in vtexts:
            if t:
                body_verses.append(f"**{v}** {t}")
        links = [f"[[{note_title}]]"]
        links += [f"[[{x}]]" for x in parent_of.get(name, [])]
        if p["kind"] == "block":
            links += [f"[[{x}]]" for x in sorted(children_of.get(name, []))]
        body = " · ".join(links) + "\n\n"
        if body_verses:
            body += "\n".join(body_verses) + "\n"
        else:
            body += "> **ESV** — _paste from Logos:_\n"
        ref_alias = (f"{p['display']} {p['ch']}:{p['v1']}" if p["v1"] == p["v2"]
                     else f"{p['display']} {p['ch']}:{p['v1']}{EN_DASH}{p['v2']}")
        front = (f"---\ntags:\n  - {p['slug']}\naliases:\n  - \"{ref_alias}\"\n"
                 f"cssclasses:\n  - verse\n---\n\n")
        bible_dir.mkdir(parents=True, exist_ok=True)
        dest.write_text(front + body, encoding="utf-8")
        created.append(name)

    # 5. append harvest list to source note (once)
    marker = "%% harvested-verse-pages %%"
    if not dry and created and marker not in text:
        with open(note, "a", encoding="utf-8") as f:
            f.write("\n## Harvested verse pages\n" + marker + "\n"
                    + " · ".join(f"[[{n}]]" for n in sorted(pages)
                                 if n in created) + "\n")

    print(f"note: {note_title}")
    print(f"verses found: {len(verses)}  |  blocks: {len(blocks)}  |  focused: {len(focused)}")
    print(f"created ({len(created)}):")
    for n in sorted(created):
        print(f"  + {n}")
    print(f"skipped existing ({len(skipped)}):")
    for n in sorted(skipped):
        print(f"  = {n}")


if __name__ == "__main__":
    main()
