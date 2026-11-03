---
name: ai-discovery
description: Use when changing the website build (scripts/build-site.py), adding a new content type, publishing a daily note, article, resource or product, or when the user asks about SEO, AI friendliness, llms.txt, robots, structured data, sharing, or getting the site found by AI models.
---

# AI Discovery — keep the site readable by people, search engines and AI models

The site is static HTML built from the Obsidian vault by `scripts/build-site.py`.
Everything an AI model needs to find and quote the teaching is produced by the build,
so new content is discoverable as soon as it is built and deployed. Never hand-edit
`site/dist`; change the build.

## What the build produces (keep all of it)

| File / feature | Purpose | Where it is made |
| --- | --- | --- |
| `<link rel="canonical">` on every page | one address per page, no duplicates | `render_page()` |
| Open Graph + Twitter tags | link previews on Facebook, X, Patreon, chat apps | `render_page()` |
| Real meta descriptions | the snippet search and AI tools show | `write(...)` desc argument |
| JSON-LD `@graph`: WebSite + Organization on every page | identity, sameAs links to Patreon, Facebook, GitHub | `render_page()` |
| JSON-LD `Article` on daily, verse, blog, resource pages | date, headline, keywords (tags) | `write(..., article=...)` |
| `robots.txt` naming GPTBot, ClaudeBot, PerplexityBot and others, allowed | AI crawlers may read and quote | end of `main()` |
| `sitemap.xml` (POSIX URLs) | discovery by search engines | end of `main()` |
| `llms.txt` | the guide: start pages plus every content URL with a one-line description | end of `main()` |
| `llms-full.txt` | all daily notes, articles and resources as plain text | `to_plain()` + end of `main()` |
| `noindex` on 404 | keeps error pages out of search | `render_page(rel=None)` |

## Rules when you change content or the build

1. **New content types** (products, courses, videos) must get: a `write(...)` call with a
   real description, an `article=` or a matching JSON-LD type (`Product` with `offers`
   when the shop opens; `VideoObject` for videos), a line in `llms.txt`, and a block in
   `llms-full.txt` if it has text.
2. **Every new daily, blog, resource or scripture-image page must appear in `llms.txt`.**
   `scripts/check_site_ai.py` fails the build check otherwise. Add the list entry in the
   same edit that adds the page. Verse pages are listed through their book index and
   the sitemap, not one by one in `llms.txt`.
3. **Descriptions** are generated from tags for daily and verse pages. Keep tags specific
   (`chaos`, `four-beasts`), not vague (`stuff`), because they feed the description,
   `keywords` and the topic pages.
4. **Frontmatter dates** must be `YYYY-MM-DD`. Articles without a valid date are skipped
   with a warning, so they do not reach the guide or the sitemap.
5. **Plain text.** `to_plain()` strips wikilinks, callout headers and comments. If a new
   syntax leaks into `llms-full.txt`, extend `to_plain()` rather than the content.
6. **Base path.** The site lives at the domain root: build with `--base=` (empty). Never
   reintroduce `/vault` in a link; the checker rejects it.
7. **Scripture text.** Use public-domain (WEB) text or link to the ESV. Never paste ESV text
   (see verse-pages rules). Reflections are the author's thoughts; the guide says so.
8. **Sharing.** New blog posts and daily notes should be shared to Patreon and Facebook
   with their site link (`https://manofgod.online/<kind>/<slug>/`). The link is the thing
   AI tools and search engines follow.

## Verify after every build

```sh
python scripts/build-site.py --base= --out=site/dist
python scripts/check_site_ai.py          # exits 1 on any failure
```

The checker confirms: required files exist; robots allows the AI crawlers and names the
sitemap; every page has a canonical and parseable JSON-LD; every daily, blog and resource
URL is in `llms.txt`; `llms-full.txt` has no wikilink or callout syntax; no `/vault` paths.
Then remove `site/` (it is git-ignored and never pushed).

## Ideas that are not built yet (ask before doing)

- Per-page social preview images (currently every page uses the logo).
- Product structured data once the shop opens.
- Submitting the sitemap to Google Search Console and Bing Webmaster Tools (a manual step
  for the site owner; Bing's index feeds several AI search tools).
- Automatic Facebook sharing of blog posts, the same way daily notes are shared.
