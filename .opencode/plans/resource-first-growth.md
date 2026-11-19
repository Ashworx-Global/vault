# Man of God: resource-first growth and community plan

Created: 2026-11-19
Status: in progress; resource scaffold created and first site usability improvements implemented locally
Owner: site author
Maintaining agent: `site-growth`
Website: https://manofgod.online/
Patreon: https://www.patreon.com/c/ManOfGodSA

## Goal and approach

Help Christian men build a Bible-reading habit, bring genuinely interested readers
to the website without ads, and invite them into ongoing conversation on Patreon.
Create useful resources first; publish and verify their destinations before
referencing them in articles, social posts, or outreach.

Reader journey:

Search / Facebook / church recommendation → useful website resource →
optional Patreon resource post and discussion → return for the next reading.

Patreon can also be a direct destination for community-oriented posts. Use the
website for searchable reading pages and a stable resource library, and Patreon
for companion downloads, discussion prompts, and community participation.
Keep the first resource freely accessible on the website; proposed Patreon
access is public/free where the platform permits. Paid extras are a later decision.

## Current evidence and open checks

- Homepage reviewed on 2026-11-19: it listed 52 daily notes, 328 verse pages,
  and 623 topics. These counts are a snapshot, not growth measurements.
- Homepage text included raw `!bible-` / `WEB-OFFLINE` fragments in previews
  and an empty resources message intended for the site author.
- No email signup was visible in the fetched homepage content; check the actual
  site and existing integrations before implementing one.
- Suggested search topics below are hypotheses, not keyword-volume research.
- `SOCIAL_PUBLISHING.md` contains conflicting setup examples, but specifically
  records Patreon API posting as unsupported and disabled. Verify current
  capabilities when implementing; do not enable that integration on assumption.
- `.opencode/commands/patreon-post.md` is an existing browser-based flow for
  Daily notes, not yet a verified resource-pack publishing workflow.
- Patreon chat availability, free-member access, download access and comment
  settings have not been checked for this account.

## Phase 1 — Create the first resource

Start here. Suggested scope: **Seven Days in the Word: A Bible Reading Plan for Men**.
Timing is relative to when work resumes; there is no launch deadline yet.

- [ ] Agree the intended reader, theme and manageable daily reading length.
- [ ] Review existing Daily notes and select suitable material with the author.
- [ ] Outline seven sessions before drafting the full pack.
- [ ] For each session include a passage reference, personal reflection, practical
  application, prayer prompt and one discussion question.
- [ ] Add an introduction explaining how an individual or men's group can use it.
- [ ] Add a one-page leader guide with a suggested meeting structure.
- [ ] Create a readable web version and a printable PDF from the approved source.
- [ ] Review biblical context, wording, attribution, readability and print layout.
  Keep personal reflection distinct from Scripture. Follow the vault's policy:
  public-domain WEB text or links to ESV, not copied ESV text.
- [ ] Prepare a brief resource description and a text-based cover/title page.

**Done when:** the author has reviewed the seven sessions, the web draft and PDF
are complete, and the PDF opens correctly on mobile and prints legibly.

Drafts may live under `.opencode/plans/drafts/` while being reviewed. Inspect the
site builder's resource conventions before choosing final published source paths.
Do not add unfinished resources to public navigation.

## Phase 2 — Establish website and Patreon destinations

Depends on Phase 1.

### Website

- [ ] Inspect resource frontmatter, build rules and download asset conventions.
- [ ] Publish the approved resource with a stable URL, descriptive title,
  introduction, seven-day outline, web reading access and download button.
- [ ] Add relevant internal links to existing readings and verse pages.
- [ ] Ensure the resource page has a suitable description, canonical URL,
  social preview metadata and inclusion in the sitemap.

### Patreon

- [ ] Check current creator-account options for public/free posts, attachments,
  free memberships, comments and community chats.
- [ ] Decide access settings explicitly. Do not describe chat as free or
  available until that access has been verified.
- [ ] Prepare a companion post with the PDF, a concise introduction,
  instructions for using it and a link to the website reading page.
- [ ] Prepare a welcome/discussion post asking which day readers are starting.
- [ ] Use a dedicated chat if supported for the intended audience; otherwise
  use a clearly identified comment thread as the initial discussion space.
- [ ] Publish through a supported workflow when requested, then record the
  exact resource-post and discussion URLs below.
- [ ] Verify the website links, PDF download and Patreon access as a visitor,
  and as a free member if that is the intended audience.
- [ ] Add “Discuss this reading on Patreon” links to the resource only after
  the destination and access instructions work.

**Done when:** the resource is usable on the website, the Patreon companion and
discussion destination work for the stated audience, and all cross-links are verified.

## Resource and destination register

Replace “pending” with verified paths/URLs as work progresses. Never invent live URLs.

| Asset | Status | Source path | Website URL | Patreon URL |
| --- | --- | --- | --- | --- |
| Seven-day reading plan | Planned | Pending | Pending | Pending |
| Printable reading pack | Planned | Pending | Pending | Pending |
| One-page leader guide | Planned | Pending | Pending | Pending |
| Welcome / discussion destination | Planned | Pending | N/A | Pending |

## Phase 3 — Make the site welcoming and retain readers

Can prepare alongside Phase 1; resource links depend on Phase 2.

- [x] Implement clearer homepage messaging:
  “Grow stronger in faith, one day at a time.”
  “Bible readings, personal reflections, and practical encouragement for Christian men.”
- [ ] Add prominent “Start here: a 7-day reading plan” and today's/latest reading actions.
- [x] Fix raw Bible/import markup in previews without altering Scripture content.
- [ ] Replace the empty resources message with the completed reading pack.
- [ ] Explain what visitors can do on Patreon, including any membership requirement.
- [ ] Decide whether to offer weekly email updates or initially use Patreon
  membership updates. Avoid building two recurring workflows before capacity is clear.
- [ ] If email is chosen, define the weekly benefit and verify signup and delivery.
- [ ] Check the mobile reader journey from homepage to download to discussion.

**Done when:** a first-time visitor can identify the site's purpose, begin reading,
and find a working way to return or join the discussion.

## Phase 4 — Publish discoverable supporting content

Depends on having a verified resource destination. Prioritise two articles first.

- [ ] How to start reading the Bible as a man.
- [ ] A 7-day Bible reading plan for busy dads.
- [ ] Bible verses about anger—with context and reflection.
- [ ] How to lead a family devotional for the first time.
- [ ] Bible study questions for a men's small group.

For each article: answer the question directly, use original practical material,
link to relevant readings and the completed resource, and offer a relevant
Patreon discussion invitation. Avoid making near-identical pages for every query.
Review the quality of existing topic archives before expanding their number.

- [ ] Check Google Search Console ownership, sitemap submission and indexing.
- [ ] Review actual search queries once data is available to refine topics.

## Phase 5 — Launch outreach and conversation

Start only when the resource and linked destinations work.

- [ ] Identify five relevant churches or men's ministry leaders for the first week.
- [ ] Write individual messages offering the free pack and asking for feedback.
- [ ] Record contact date, response, feedback and agreed follow-up.
- [ ] Publish up to three useful Facebook posts per week, as capacity permits:
  scripture reference, short reflection, practical action and discussion question.
- [ ] Link resource-discovery posts to the website; link discussion invitations
  directly to the relevant Patreon post/chat rather than a generic profile.
- [ ] Participate helpfully in relevant groups and follow their sharing rules.
- [ ] Host one weekly Patreon question and respond to genuine contributions.
- [ ] Invite readers to share the pack with one friend or their men's group.

Outreach draft, to personalise after the resource exists:

> Hi [name], I publish Bible readings and personal reflections for Christian men
> at Man of God. I've put together a free seven-day study with discussion questions
> and a printable leader guide. Would you be willing to look at it and tell me
> whether it would help your group? [verified resource URL]

## Phase 6 — Review and improve

Review weekly during the first four weeks after launch, then monthly.
Record a baseline when launching; unavailable metrics should be marked unknown.

| Measure | Source / method | Baseline | Latest |
| --- | --- | --- | --- |
| Search impressions and clicks | Google Search Console | Unknown | Unknown |
| Resource visits and downloads | Existing reporting, if available | Unknown | Unknown |
| Patreon resource views and free joins | Available creator reporting | Unknown | Unknown |
| Meaningful discussion participants | Manual weekly count | Unknown | Unknown |
| Church/group responses and use | Outreach log | Unknown | Unknown |
| Repeat readers / email signups | Available reporting, if implemented | Unknown | Unknown |

Use existing reporting first. New tracking is a separate author decision and is
outside the current site-growth agent's permissions. Do not infer download counts
from page views or promise traffic/ranking results.

Choose the next resource based on reader questions and group feedback. Possible
follow-ups: a family devotional starter, an anger-and-self-control study, or a
men's group discussion pack. Build one at a time.

## Resume instructions

Open OpenCode in `/home/macmint/Dev/vault` and ask:

> Use site-growth to resume `.opencode/plans/resource-first-growth.md`.
> Review its progress and help me outline the seven-day reading resource first.

The agent maintains this plan and drafts within its permissions. The author or
an appropriately authorised writing session handles published content changes.
For planning-only work, skip the full site-health workflow. Run the build and
checker when implementing site changes, following the existing agent instructions.

At the end of each work session:
1. Update checkboxes and resource status only for completed, verified work.
2. Record paths and live URLs separately from proposed destinations.
3. Log decisions, blockers and the next concrete action below.

## Progress log

### 2026-11-19 — Plan registered

- Saved a resource-first sequence and proposed Patreon community journey.
- Linked this plan to the existing `site-growth` agent.
- No resources, public posts, outreach or website changes have been completed.
- Next action: agree the seven-day theme and outline using existing Daily notes.
- Open decisions: first theme, Patreon audience/chat access, and email versus
  Patreon updates for the initial launch.

### 2026-11-19 — Resource structure and export workflow

- Created `Resources/Seven-Days-in-the-Word/` with metadata, introduction,
  seven `day-NN/reading.md` folders, leader guide and production instructions.
- Added `scripts/build-reading-plan.py` for A5 PDF, reflowable EPUB and CBZ
  rendered from PDF pages. Draft previews are separate from release exports.
- Content remains placeholder scaffolding awaiting the author's selections.
- Added website/Patreon cross-link metadata; specific resource URLs are pending.
- Amazon/Kindle distribution is proposed. Verify current free-pricing options,
  external-link rules and exclusivity terms before committing to that channel.
- Website download integration follows content completion; the current builder
  does not automatically publish these nested resource files.
- Next action: select passages and draft Day 1 with the author.

### 2026-11-19 — First usability implementation

- Simplified the header to Readings, Resources, About and an accessible Explore menu.
- Replaced the long homepage introduction with clear messaging and a latest-reading
  action; reduced reading cards to three and moved exploration into three next steps.
- Removed homepage count panels, the large verse listing and unrelated blog feed;
  their full pages remain available through navigation.
- Suppressed the homepage's empty ranked-resources section. The completed reading
  pack and its start-here/download links remain pending.
- Cleaned preview text to omit Bible-import callouts, vault comments, standalone
  reference links and headings, and to show the first readable paragraph.
- Improved daily reading line length, labelled the reading search, added a
  no-results message and clarified newer/older navigation.
- Corrected the daily/blog Patreon destination and added a homepage follow section.
  Chat access remains unverified; the site does not promise it.
- Verified: full build, discoverability checker (1,049 pages), five regression
  tests, rendered homepage review, 375px/1280px iframe layout checks without
  horizontal overflow, and search no-results/reset behaviour (52 readings restored).
- Changes are local, awaiting review and deployment. No traffic improvement has
  been measured. Full mobile resource/download/discussion journey awaits publication.

### 2026-11-19 — Invite readers into Patreon conversations

- Author confirmed that the same readings and conversations are on Patreon.
- Updated homepage and daily-reading calls to action to explain the benefit:
  discuss the reading, share reflections and ask questions.
- Added short account/joining guidance, using the existing creator-page URL.
- Membership pricing and free access remain unconfirmed; clarify these before
  adding “Join free” wording.
- Next improvement: record each reading's actual Patreon post URL and link
  directly to its discussion rather than requiring a title search.

### 2026-11-19 — Upcoming projects preview

- Added a brief “In the works” section within the homepage Patreon invitation.
- Author-provided projects: daily devotionals, comic books, animations, manly
  soaps, shirts, braai gear and other goods for men.
- Copy describes work in progress and invites ideas on Patreon without promising
  release dates, current stock or membership benefits.
