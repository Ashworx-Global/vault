# Social Publishing Setup

Your vault now automatically publishes daily notes and art projects to Patreon and Facebook.

## Setup

### 1. GitHub Secrets (already done)
- ✅ `PATREON_API_TOKEN` - Your Patreon creator API token

### 2. Add Facebook Page Token
GitHub → Repository → Settings → Secrets → New repository secret:
- Name: `FACEBOOK_PAGE_TOKEN`
- Value: [Get from Facebook](https://developers.facebook.com/docs/facebook-login/access-tokens)
  - Go to Facebook App Dashboard → Tools → Access Token Tool
  - Or use your page permanent access token

### 3. Add Facebook Page ID (as variable, not secret)
GitHub → Repository → Settings → Variables → New repository variable:
- Name: `FACEBOOK_PAGE_ID`
- Value: `61596013522180`

## How It Works

**On each git push:**
1. GitHub Actions builds your site (scripts/art_processor.py, scripts/build-site.py)
2. After successful build, scripts/social_publisher.py runs
3. New daily notes are posted to Patreon + Facebook
4. New art projects are posted to Patreon + Facebook
5. Existing art projects are updated when you add more images
6. Published content is tracked in `.published-content.json` to prevent duplicates

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

If you want to skip publishing for a commit, just don't push. Publishing only runs on GitHub Actions.

## Troubleshooting

**"PATREON_API_TOKEN not set"**
- Add the secret to GitHub repo settings

**"FACEBOOK_PAGE_TOKEN not set"**
- Add the secret to GitHub repo settings

**"FACEBOOK_PAGE_ID not set"**
- Add the variable to GitHub repo settings (use `61596013522180`)

**Posts not appearing**
- Check GitHub Actions logs for errors
- Verify tokens are correct and have proper permissions
- Patreon: Token must have "creator" scope
- Facebook: Token must have "pages_manage_posts" permission

## Manual Publishing

To publish manually without pushing:
```bash
PATREON_API_TOKEN=your_token \
FACEBOOK_PAGE_TOKEN=your_token \
FACEBOOK_PAGE_ID=61596013522180 \
python3 scripts/social_publisher.py
```
