---
description: Harvest a Daily devotional note into linked Bible verse pages with tags, then commit and push.
---

Run the verse-pages skill workflow against one Daily note in the Obsidian vault.

Argument: $ARGUMENTS — a Daily note identifier, e.g. `2026-10-02` or `2026-10-02 ( When Love Is Lost, Labor Is in Vain)`.

Vault: `/Volumes/Data/AshworX-Files/AshworX-Vault` (remote `https://github.com/Ashworx-Global/vault.git`, branch `main`).

Steps:

1. **Resolve the note.** Glob `Daily/*$ARGUMENTS*` in the vault. If zero or multiple matches, stop and ask the user. Read the note fully.
2. **Ensure harvestable reading links.** The harvester (`.opencode/skills/verse-pages/harvest_verses.py`, run from the vault root) builds reading-block pages ONLY from markdown links `[ref](url)` in the note — it ignores the `> [!bible]- ... - WEB-OFFLINE` callout headers (its header regex requires `- ESV]`). If the note's first lines list readings as plain text with no `ref.ly` links, prepend one link line in this format:
   `[Eze 3:16–5:17](https://ref.ly/logosres/esv?ref=BibleESV.Eze3.16) * [Rev 2:1–11](https://ref.ly/logosres/esv?ref=BibleESV.Re2.1) * [Job 32:11–22](https://ref.ly/logosres/esv?ref=BibleESV.Job32.11)`
   Use short refs the parser knows (`Eze`, `Rev`, `Zec`, `Ac`, `Mal`, `Job`). NEVER use bare `Re` for Revelation — the parser has no `re` key, so use `Rev` in link text (the URL may keep Logos' own `Re` abbrev). Report any link line you add.
3. **Dry-run, then harvest.** Run `python3 .opencode/skills/verse-pages/harvest_verses.py --dry-run "<note>"`, show the planned pages, then run it for real. NEVER overwrite an existing `Bible/` page — report skips.
4. **Refinement pass.** Read each created page and upgrade it to hand-made quality:
   - Tags (all lowercase): keep the book slug; add 2–5 thematic tags drawn from the actual verse content and the daily reflection (e.g. `watchman`, `first-love`, `breath-of-god`).
   - Aliases: keep the `Book C:V` resolvable alias; add one thematic Title Case alias (e.g. `Watchman To Israel`).
   - Cross-links: append related pages on the backlink line with `·` (block ↔ focused pages, sequential passages, e.g. `[[Acts 27 v 1–44]]`, `[[Revelation 1 v 1–20]]`).
5. **Daily note frontmatter.** Prepend thematic tags (lowercase) matching the note's threads. `---` MUST be line 1 — if the file starts with blank lines, remove them in the same edit (a leading blank line breaks frontmatter parsing and renders tags as page text).
6. **Verify the site build.** Run `python3 scripts/build-site.py --base /vault --out site/dist` in the vault and confirm the page count grew; spot-check the new `bible/...` and `daily/...` URLs exist. Then `rm -rf site` (build output is git-ignored, never pushed).
7. **Commit and push.** Stage ONLY `Bible/` and `Daily/` (never `.obsidian/` editor noise). Commits MUST be GPG-signed with message `vault: harvest verse pages for <YYYY-MM-DD>`. The shell needs `export PATH="/usr/local/bin:$PATH"` for `gpg`, plus `eval "$(grep '^export GPG=' ~/.zshrc)"` and `export GPG_TTY=$(tty 2>/dev/null || echo ${TTY:-})`. Then `git push` (push auto-triggers the Pages deploy).
