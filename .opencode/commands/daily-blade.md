---
description: Extract a Daily devotional note into linked Bible verse pages with tags, verify the vault site, commit and push using this repository's local GPG key, then post it to Patreon through the browser.
---

Run the verse-pages skill workflow against one Daily note in the current
Obsidian vault.

Argument: $ARGUMENTS - a Daily note identifier, for example `2026-10-02` or
`2026-10-02 (When Love Is Lost, Labor Is in Vain)`.

Vault: the current Git worktree (remote `origin`, branch `main`). Run every
command from the repository root.

Steps:

1. **Resolve the note.** Glob `Daily/*$ARGUMENTS*`. If zero or multiple matches, stop and ask the user. Read the note fully, including frontmatter, readings, and reflection, before changing anything.
2. **Ensure harvestable reading links.** The harvester (`.opencode/skills/verse-pages/harvest_verses.py`, run from the vault root) builds reading-block pages from Bible callout headers with any translation label and from markdown links `[ref](url)`. If the note's first lines list readings as plain text with no Bible callouts or `ref.ly` links, prepend one link line in this format:
   `[Eze 3:16-5:17](https://ref.ly/logosres/esv?ref=BibleESV.Eze3.16) * [Rev 2:1-11](https://ref.ly/logosres/esv?ref=BibleESV.Re2.1) * [Job 32:11-22](https://ref.ly/logosres/esv?ref=BibleESV.Job32.11)`
   Use short refs the parser knows (`Eze`, `Rev`, `Zec`, `Ac`, `Mal`, `Job`). NEVER use bare `Re` for Revelation - the parser has no `re` key, so use `Rev` in link text (the URL may keep Logos' own `Re` abbreviation). Report any link line you add.
3. **Dry-run, then harvest.** Run `python3 .opencode/skills/verse-pages/harvest_verses.py --dry-run "<note>"`, show the planned pages, then run it for real. NEVER overwrite an existing `Bible/` page - report skips.
4. **Refinement pass.** Read each created page and upgrade it to hand-made quality:
   - Tags (all lowercase): keep the book slug; add 2-5 thematic tags drawn from the actual verse content and the daily reflection (for example, `watchman`, `first-love`, `breath-of-god`).
   - Aliases: keep the `Book C:V` resolvable alias; add one thematic Title Case alias (for example, `Watchman To Israel`).
   - Cross-links: append related pages on the backlink line with `·` (block <-> focused pages, sequential passages, for example, `[[Acts 27 v 1-44]]`, `[[Revelation 1 v 1-20]]`).
5. **Daily note frontmatter.** Prepend thematic tags (lowercase) matching the note's threads. `---` MUST be line 1 - if the file starts with blank lines, remove them in the same edit (a leading blank line breaks frontmatter parsing and renders tags as page text).
6. **Verify the site build.** Run `python3 scripts/build-site.py --base=/vault --out=site/dist` (note: `--out` needs the `=` form) and confirm the page count grew; spot-check the new `bible/...` and `daily/...` URLs exist. Then remove `site/` (build output is git-ignored and never pushed).
7. **Commit and push.** Stage ONLY the changed `Bible/` and `Daily/` files (never `.obsidian/` editor noise). Confirm `git config --local --get user.signingkey` returns a key and `git config --local --get commit.gpgsign` returns `true`. Commits MUST be GPG-signed with message `vault: harvest verse pages for <YYYY-MM-DD>`. Set `GPG_TTY`, commit explicitly with `-S`, verify with `git log -1 --show-signature`, then `git push origin main` (push auto-triggers the Pages deploy). Do not source a shell profile or modify global Git/GPG configuration: this repository's local `gpg.program` wrapper and signing key are authoritative.
8. **Post to Patreon (browser).** The Patreon API is read-only, so this is done in the user's default browser, which is already signed in. Do this only after step 7's push succeeded. Branch on the platform:
   - **Windows:** skip the AppleScript flow below, but keep the Patreon intent
     gate (`--no-patreon` in `$ARGUMENTS` skips this step). Run the Patreon
     build exactly as the `patreon-post` command does:
     `pwsh scripts/patreon_post.ps1 "<note path>" -Open -Copy`
     It prints JSON (`title`, `date`, `tags`, `site_url`), opens the interactive
     `post.html` review page in the default browser and puts the formatted body
     on the clipboard. The article is editable, so click into it, type any extra
     comments the user asks for, then press **Copy post body** and paste
     (Ctrl+V) into the Patreon body editor. Use the review page buttons for the
     other composer fields: title, tags (comma list), site URL, publish date.
     Open `https://www.patreon.com/c/ManOfGodSA`, click "Make your first post" /
     "Create" / "Make a post", fill and re-read each field as described, and
     stop and report if any field cannot be confirmed. Skip the AppleScript
     instructions below.
   - **macOS:**
   - Build the post: `python3 scripts/patreon_post.py "<note path>" --out "$TMPDIR/patreon-<YYYY-MM-DD>" --copy`. It prints JSON (`title`, `date`, `tags`, `site_url`) and puts the formatted body on the clipboard. The body is the intro, then per reading a heading linked to its `[!bible]` BibleGateway link, the quoted verses with their `ref.ly` links, and the user's comments, then the site link. The site link is `https://ashworx-global.github.io/vault/daily/<slugified note name>/`, for example `.../daily/2026-10-19-big-picture-hope/`. Do not paste the full verse text from the callouts.
   - Open `https://www.patreon.com/c/ManOfGodSA` in the default browser (`open`; at the time of writing that is Edge) and click "Make your first post" or "Create"/"Make a post", whichever the page shows. Drive the page with AppleScript `execute javascript` (Edge/Chrome need View > Developer > Allow JavaScript from Apple Events). If that is not enabled, stop and tell the user rather than guessing at coordinates.
   - Fill in: title = `title`; body = paste the clipboard (Cmd+V) and check the links and headings survived; "Add tags" = the `tags` list; audience = leave on the default free option and confirm it reads free; "Set publish date" = `date`.
   - Inspect the real DOM for each control before using it, and re-read the field afterwards to confirm it took. If any field cannot be confirmed, stop before publishing and report which one.
   - Click Publish, then confirm the post appears on the creator page. Report the post URL. Never retry Publish blindly: check the creator page first so a post is not duplicated.
   - Skip this step and say so if the user passed no Patreon intent (`--no-patreon` in `$ARGUMENTS`).
