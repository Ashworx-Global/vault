# Seven Days in the Word

A seven-day Bible reading plan for men. **Draft scaffold: readings have not yet
been selected or written.**

## Source structure

- `book.json`: title, author, language, publication status and verified links.
- `introduction.md`: welcome and instructions.
- `day-01/reading.md` through `day-07/reading.md`: one session per folder.
- `leader-guide.md`: guidance for a men's group.
- `exports/`: generated PDF, EPUB and CBZ (ignored by Git).

Write ordinary Markdown with standard Markdown links. Use WEB Scripture text or
link to ESV; do not paste ESV text. Keep personal reflection clearly distinguished
from Scripture. The initial renderer supports text and links; images, Obsidian
embeds and wikilinks are not supported. Add image packaging before using artwork.

## Build

Install Python dependencies into your preferred virtual environment:

```sh
python3 -m pip install -r scripts/requirements-reading-plan.txt
```

CBZ creation also requires Poppler's `pdftoppm` executable (Ubuntu/Linux Mint:
`sudo apt install poppler-utils`). WeasyPrint may need system libraries; consult
its installation instructions if the renderer reports missing libraries.

From the vault root:

```sh
python3 scripts/build-reading-plan.py --preview
```

Preview exports are visibly labelled DRAFT. After completing and reviewing all
content, remove `TODO:` placeholders, set `status` to `ready` in `book.json`, and run:

```sh
python3 scripts/build-reading-plan.py
```

The PDF uses A5 reading pages, suitable for printing with a PDF viewer's booklet
setting. It is not pre-imposed printer spreads. EPUB is reflowable with navigation;
CBZ contains numbered PNG images of the exact PDF pages. Build all three from the
same approved source. Validate the EPUB with EPUBCheck and Kindle Previewer before
uploading; these checks are not replaced by a successful export.

## Publication checklist

- [ ] Finish seven readings, introduction and leader guide; author review.
- [ ] Fill in the actual author and rights statement in `book.json`.
- [ ] Inspect PDF page breaks, EPUB navigation and CBZ page order.
- [ ] Create the website landing page and download hosting.
- [ ] Publish a Patreon companion/download post; verify intended access.
- [ ] Add verified resource and discussion URLs to `book.json` and rebuild.
- [ ] Upload the final downloads and cross-link website and Patreon.
- [ ] Research current Amazon KDP pricing, external-link and distribution rules.
- [ ] Validate EPUB in Kindle Previewer and review rights/metadata requirements.
- [ ] Decide whether Amazon fits the free distribution goal before enrolling.

The website builder currently discovers only top-level `Resources/*.md`; this
nested source folder is not automatically a public resource or download page.
Website integration is a follow-up task once the content is ready.

Amazon/Kindle is a proposed distribution channel, not a confirmed free listing.
Verify current minimum prices, free-promotion/price-matching options and any
exclusivity terms (especially KDP Select) before distributing the same ebook
through Patreon and the website. CBZ is a reader download, not the Kindle upload.
Use helpful contextual cross-links rather than links added solely for rankings.

Only put actual published URLs in `book.json`. Initially the book links to the
existing website and Patreon profile; add resource-specific URLs when available.
Final Amazon-specific editions may need adjusted links to meet current rules.

Plan: `.opencode/plans/resource-first-growth.md`.
