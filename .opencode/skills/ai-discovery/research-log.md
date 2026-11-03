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
