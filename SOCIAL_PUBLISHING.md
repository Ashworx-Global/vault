# Social Publishing Setup

Your vault now automatically publishes daily notes and art projects to Patreon and Facebook.

## Setup

### 1. GitHub Secrets
- ✅ `PATREON_API_TOKEN` - Your Patreon creator API token
- Add `FACEBOOK_PAGE_TOKEN` - Your Facebook page access token

### 2. GitHub Variables
- Add `FACEBOOK_PAGE_ID` - Your Facebook page ID (numeric)
- Optionally add `PUBLISH_PATREON` (default: `true`)
- Optionally add `PUBLISH_FACEBOOK` (default: `true`)

## Feature Flags

You can enable/disable publishing to each platform independently via GitHub Variables:

### Publishing Flags

Go to **Settings → Variables** and add (or edit):

| Variable | Default | Values | Purpose |
|----------|---------|--------|---------|
| `PUBLISH_PATREON` | `true` | `true`, `false` | Enable/disable Patreon publishing |
| `PUBLISH_FACEBOOK` | `true` | `true`, `false` | Enable/disable Facebook publishing |

### Examples

**Disable Facebook (while debugging):**
```
PUBLISH_FACEBOOK = false
PUBLISH_PATREON = true
```

**Disable all publishing temporarily:**
```
PUBLISH_PATREON = false
PUBLISH_FACEBOOK = false
```

**Re-enable after fix:**
```
PUBLISH_PATREON = true
PUBLISH_FACEBOOK = true
```

## How It Works

**On each git push:**
1. GitHub Actions builds your site
2. After successful build, scripts/social_publisher.py runs
3. Checks enabled platforms (via `PUBLISH_PATREON` and `PUBLISH_FACEBOOK`)
4. New daily notes are posted to enabled platforms
5. New art projects are posted to enabled platforms
6. Existing art projects are updated when you add more images
7. Published content is tracked to prevent duplicates

## What Gets Posted

### Daily Notes
- Full note content with all Bible verses
- Link back to: `https://ashworx-global.github.io/vault/daily/{date}/`
- Posted as: `[Title]` on Patreon, first 500 chars on Facebook

### Art Projects
- Project README content
- Image count (updated when you add more images)
- Link to: `https://ashworx-global.github.io/vault/art/{project-slug}/`
- Art projects are always updated (so viewers see progress)

## Disabling Publishing

To skip all publishing without editing variables, delete the secrets/variables from GitHub.

For a single push, you can also disable in variables temporarily and re-enable later.

## Troubleshooting

**"PATREON_API_TOKEN not set"**
- Add to GitHub repo Settings → Secrets

**"FACEBOOK_PAGE_TOKEN not set"**
- Add to GitHub repo Settings → Secrets

**"FACEBOOK_PAGE_ID not set"**
- Add to GitHub repo Settings → Variables

**Posts not appearing**
- Check GitHub Actions logs for errors
- Verify tokens are correct and have proper permissions
- Check the feature flags (`PUBLISH_PATREON`, `PUBLISH_FACEBOOK`)

**Patreon 405 errors**
- Token may lack creator permissions
- Verify at https://www.patreon.com/settings/apps

**Facebook 400 errors**
- Token may lack `pages_manage_posts` permission
- Disable with `PUBLISH_FACEBOOK = false` and debug separately

## Manual Publishing

To publish manually without pushing:
```bash
PATREON_API_TOKEN=your_token \
FACEBOOK_PAGE_TOKEN=your_token \
FACEBOOK_PAGE_ID=61596013522180 \
PUBLISH_PATREON=true \
PUBLISH_FACEBOOK=false \
python3 scripts/social_publisher.py
```

All publishing flags are optional and default to `true` if not set.
