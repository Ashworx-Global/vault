# AI discovery research log

Append-only. Each entry: date, finding, source URL, adopted or not, and why. The
site-growth agent writes here after each research pass.

## 2026-11-03 — baseline (set up by the author's assistant)

- **Adopted:** llms.txt at the site root with start pages and every content URL; llms-full.txt
  with all text content. Source: https://llmstxt.org
- **Adopted:** robots.txt that explicitly allows AI crawlers and names the sitemap.
  Sources: vendor crawler documentation (OpenAI GPTBot / OAI-SearchBot, Anthropic ClaudeBot,
  Perplexity, Google-Extended). Verify the current user-agent names before each change.
- **Adopted:** JSON-LD (schema.org WebSite, Organization, Article, Person). Source:
  https://developers.google.com/search/docs/appearance/structured-data
- **Adopted:** canonical links, Open Graph and Twitter card tags, meta descriptions.
- **Adopted:** XML sitemap with POSIX URLs. Source: https://www.sitemaps.org
- **Pending:** submit the sitemap to Google Search Console and Bing Webmaster Tools (owner
  action). Bing Webmaster Tools also offers IndexNow for pushing URL changes.
- **Pending:** per-page social preview images.
- **Pending:** Product structured data when the shop opens.

## 2026-11-03 — first run of the ai-discovery review

- **Google AI features:** no extra requirements; normal SEO applies; structured data must match
  visible text. Source: https://developers.google.com/search/docs/appearance/ai-features
  Adopted: nothing new needed (the existing SEO and structured data already follow it).
- **llms.txt v2:** clean markdown copy at page address + `index.md`; `rel="alternate"
  type="text/markdown"` and `rel="describedby"` links; links in llms.txt point at the markdown.
  Source: https://llmstxt.org . **Adopted:** `index.md` copies for daily, blog, resource and
  standalone pages; alternate and describedby links; llms.txt links the copies; checker verifies.
- **OpenAI crawlers:** OAI-SearchBot (search), GPTBot (training), ChatGPT-User (user-initiated,
  robots may not apply). Source: https://developers.openai.com/api/docs/bots . **Adopted:** nothing
  changed. Open question for the author: allow or block GPTBot training.
- **IndexNow:** key file at domain root, URL submission per change, supported by Bing. Source:
  https://www.indexnow.org/documentation . **Not adopted yet:** needs owner approval (see SKILL.md).
- **Health:** build 298 pages (37 daily, 261 verse); checker ok, 815 pages, 38 content URLs with markdown copies.
- **IndexNow, adopted (owner approved 2026-11-03):** key file served at the root, full sitemap
  submitted to api.indexnow.org after each deploy. Source: https://www.indexnow.org/documentation
  Checker verifies the key file is served.
