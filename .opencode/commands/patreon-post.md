---
description: Build the Patreon post for one Daily note, open the interactive review page, then create and verify the Patreon post in the browser.
---

Build the Patreon post pieces for one Daily note and post them to Patreon
through the browser.

Argument: $ARGUMENTS - a Daily note identifier, for example `2026-10-19`
or `2026-10-19 (Big Picture Hope)`. Everything after an optional separator
`--` is comment text to add to the post (retros, private notes).

Vault: the current Git worktree. Run every command from the repository root.

Steps:

1. **Resolve the note.** Glob `Daily/*$ARGUMENTS*` (match on the part before
   `--` only). If zero or multiple matches, stop and ask the user. Work out
   the note's date part (`YYYY-MM-DD`) from its name.
2. **Build the post.** Run
   `pwsh scripts/patreon_post.ps1 "<note path>" -Open -Copy` It prints a
   JSON line with `title`, `date`, `tags`, `site_url`, writes
   `post.html` / `post-body.html` / `post.json` into
   `%TEMP%\patreon-<YYYY-MM-DD>` (or the directory given with `-Out`), opens
   the review page in the default browser and puts the formatted body on the
   clipboard as rich text. Report the JSON values to the user.
3. **Inject comments, if any.** If `$ARGUMENTS` included text after `--`,
   insert it as `<p>comment</p>` paragraph(s) in the editable article of the
   generated `post.html` (create it with `-Out` first if you need to place it
   before opening). Re-open the page afterwards if you edited with the page
   closed. Tell the user where you placed it.
4. **Create the post in the browser.** Open `https://www.patreon.com/c/ManOfGodSA`
   and click "Make your first post" / "Create" / "Make a post", whichever the
   page shows. Then fill in the composer:
   - Title = `title` (or **Copy title** on the review page).
   - Body = with the cursor in the body editor, **Ctrl+V** (the clipboard
     already holds the formatted body, or press **Copy post body** first to
     capture any comment the user typed into the editable article). Check the
     headings and links survived the paste.
   - "Add tags" = the `tags` list (**Copy tags** copies them comma-separated).
   - Audience = leave on the default free option and confirm it reads free.
   - "Set publish date" = `date` (**Copy date**).
   Inspect the real DOM for each control before using it, and re-read the
   field afterwards to confirm it took. If any field cannot be confirmed,
   stop before publishing and report which one.
5. **Publish, then verify.** Click Publish, then confirm the post appears on
   the creator page and report the post URL. Never retry Publish blindly:
   check the creator page first so a post is not duplicated.
6. **Skip this step** and say so if the user passed `--no-patreon` in
   `$ARGUMENTS`.
