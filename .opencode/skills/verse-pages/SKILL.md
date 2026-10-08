---
name: verse-pages
description: Use when user says harvest verses, scrape verses, verse pages, or asks to turn Bible reading in a daily note into linked Bible verse pages. Parses refs and creates vault pages with tags and aliases.
---

# Verse Pages — Harvest Bible Passages into Linked Notes

Turns a daily/study note's Bible readings (Bible Verse plugin callouts,
Logos links, short refs like `Zec 7:5`) into one page per passage in
`Bible/`, following vault conventions. Reusable via the helper script —
the agent adds the theological judgment (theme tags, thematic alias).

## Helper script (run from the vault root)

`.opencode/skills/verse-pages/harvest_verses.py`

```sh
python3 .opencode/skills/verse-pages/harvest_verses.py "Daily/<note>.md"
python3 .opencode/skills/verse-pages/harvest_verses.py --dry-run "Daily/<note>.md"  # plan only
```

What it does:
- Parses `> [!bible]- [Book C:V-R - ESV]` headers and splits multi-chapter
  ranges into per-chapter block pages (using verses actually present).
- Parses per-verse lines `> [[Book C#^V|V]]. text` for verse content.
- Parses own-line short refs (`Zec 7:5`, `Ac 23:21–22`) and ref-like
  markdown link texts (`[Zec 7:5](https://ref.ly/...)`, `[Job 29:13–25]()`)
  into focused-verse pages.
- Page name: `<Book> <C> v <R>` (`–` en dash for ranges).
- Frontmatter: lowercase book-slug tag, resolvable `Book C:V` alias,
  `cssclasses: verse`. Verse text harvested from the note; ESV-paste
  placeholder when the text isn't in the note.
- Cross-links block ↔ focused pages sharing book+chapter, backlinks the
  source note, and appends a `## Harvested verse pages` section to the
  source note (once, via marker).
- NEVER overwrites existing pages — reports them as skipped.

## Agent refinement pass (after running the script)

For each created page, read it and upgrade like the hand-made verse pages:

1. **Tags** (all lowercase): keep the book slug; add 2–5 thematic tags from
   the actual verse content (e.g. `trust`, `horses`, `courage`, `fasting`).
2. **Alias**: keep the `Book C:V` alias; prepend/keep one thematic Title Case
   alias drawn from the verse (e.g. `Take Courage`).
3. **Links**: keep script backlinks; add links to related existing pages
   (people, themes, books) where genuine.
4. Verify with `ls Bible/` + grep that every planned page exists once.

## Rules

- NEVER overwrite an existing `Bible/` page — the user may have pasted ESV
  text or hand-tuned tags there. Report skips.
- NEVER invent verse text. Text comes from the note, the ESV API only with
  an explicit key, else the `> **ESV** — _paste from Logos:_` placeholder.
- Page names use `v` and en dash: `Luke 3 v 27`, `Isaiah 40 v 29–31`.
- Tags lowercase; thematic alias Title Case; `cssclasses: verse` always.
