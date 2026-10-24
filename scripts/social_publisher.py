#!/usr/bin/env python3
"""Publish vault content to Patreon and Facebook.

Posts daily notes with Bible verses and art projects to social platforms.
Tracks published content to avoid duplicates and supports updates.

Environment variables:
  PATREON_API_TOKEN    Patreon creator token
  FACEBOOK_PAGE_TOKEN  Facebook page access token
  FACEBOOK_PAGE_ID     Facebook page ID (numeric)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


class PublishedContent:
    """Track published content across platforms."""
    
    def __init__(self, track_file: Path):
        self.track_file = track_file
        self.data = self._load()
    
    def _load(self) -> dict:
        if self.track_file.exists():
            return json.loads(self.track_file.read_text())
        return {"daily": {}, "art": {}, "patreon": {}, "facebook": {}}
    
    def save(self):
        self.track_file.write_text(json.dumps(self.data, indent=2))
    
    def get_patreon_post_id(self, content_type: str, slug: str) -> Optional[str]:
        """Get Patreon post ID for content (to update instead of create)."""
        key = f"{content_type}:{slug}"
        return self.data.get("patreon", {}).get(key)
    
    def get_facebook_post_id(self, content_type: str, slug: str) -> Optional[str]:
        """Get Facebook post ID for content."""
        key = f"{content_type}:{slug}"
        return self.data.get("facebook", {}).get(key)
    
    def set_patreon_post_id(self, content_type: str, slug: str, post_id: str):
        """Track published Patreon post."""
        if "patreon" not in self.data:
            self.data["patreon"] = {}
        self.data["patreon"][f"{content_type}:{slug}"] = post_id
        self.save()
    
    def set_facebook_post_id(self, content_type: str, slug: str, post_id: str):
        """Track published Facebook post."""
        if "facebook" not in self.data:
            self.data["facebook"] = {}
        self.data["facebook"][f"{content_type}:{slug}"] = post_id
        self.save()
    
    def is_published(self, content_type: str, slug: str) -> bool:
        """Check if content has been published anywhere."""
        key = f"{content_type}:{slug}"
        return key in self.data.get("patreon", {}) or key in self.data.get("facebook", {})


def strip_html_tags(html: str) -> str:
    """Convert HTML to plain text, preserving basic formatting."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = html.replace('</p>', '\n\n').replace('<br>', '\n').replace('<br/>', '\n')
    html = re.sub(r'<[^>]+>', '', html)
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<')
    html = html.replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    html = '\n'.join(line.strip() for line in html.split('\n') if line.strip())
    return html.strip()


def publish_to_patreon(title: str, content_text: str, published_content: PublishedContent,
                       content_type: str, slug: str) -> Optional[str]:
    """Publish or update post on Patreon. Returns post ID if successful."""
    token = os.getenv("PATREON_API_TOKEN")
    if not token:
        print("⚠ PATREON_API_TOKEN not set, skipping Patreon")
        return None
    
    try:
        import requests
    except ImportError:
        print("⚠ requests library not found")
        return None
    
    post_id = published_content.get_patreon_post_id(content_type, slug)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get campaign ID
    try:
        resp = requests.get("https://www.patreon.com/api/oauth2/v2/campaigns", headers=headers)
        if resp.status_code != 200:
            print(f"  ✗ Patreon: Failed to get campaign ({resp.status_code})")
            return None
        campaigns = resp.json().get("data", [])
        if not campaigns:
            print("  ✗ Patreon: No campaigns found")
            return None
        campaign_id = campaigns[0]["id"]
    except Exception as e:
        print(f"  ✗ Patreon: Error fetching campaign: {e}")
        return None
    
    payload = {
        "data": {
            "type": "post",
            "attributes": {
                "title": title,
                "content": content_text,
                "is_public": True
            }
        }
    }
    
    url = f"https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/posts"
    
    if post_id:
        url = f"https://www.patreon.com/api/oauth2/v2/posts/{post_id}"
        print(f"📝 Updating Patreon: {title}")
        resp = requests.patch(url, json=payload, headers=headers)
    else:
        print(f"📢 Publishing to Patreon: {title}")
        resp = requests.post(url, json=payload, headers=headers)
    
    if resp.status_code in [200, 201]:
        data = resp.json()
        post_id = data.get("data", {}).get("id")
        if post_id:
            published_content.set_patreon_post_id(content_type, slug, post_id)
            print(f"  ✓ Posted to Patreon")
            return post_id
    else:
        print(f"  ✗ Patreon failed: {resp.status_code}")
    
    return None


def publish_to_facebook(title: str, content_text: str, url_link: str,
                       published_content: PublishedContent,
                       content_type: str, slug: str) -> Optional[str]:
    """Publish or update on Facebook page. Returns post ID if successful."""
    token = os.getenv("FACEBOOK_PAGE_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    if not token or not page_id:
        print("⚠ FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID not set, skipping Facebook")
        return None
    
    try:
        import requests
    except ImportError:
        return None
    
    post_id = published_content.get_facebook_post_id(content_type, slug)
    
    message = f"{title}\n\n{content_text}\n\n🔗 {url_link}"
    payload = {
        "message": message,
        "access_token": token
    }
    
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    
    if post_id:
        url = f"https://graph.facebook.com/v18.0/{post_id}"
        print(f"📝 Updating Facebook: {title}")
        resp = requests.post(url, data=payload)
    else:
        print(f"📢 Publishing to Facebook: {title}")
        resp = requests.post(url, data=payload)
    
    if resp.status_code in [200, 201]:
        data = resp.json()
        post_id = data.get("id")
        if post_id:
            published_content.set_facebook_post_id(content_type, slug, post_id)
            print(f"  ✓ Posted to Facebook")
            return post_id
    else:
        print(f"  ✗ Facebook failed: {resp.status_code}")
    
    return None


def get_daily_notes(daily_dir: Path) -> list[tuple[str, str, str]]:
    """Get list of daily notes (slug, title, date). Returns: [(slug, title, date_str), ...]"""
    notes = []
    for md_file in sorted(daily_dir.glob("*.md"), reverse=True):
        slug = md_file.stem
        if re.match(r'\d{4}-\d{2}-\d{2}', slug):
            content = md_file.read_text()
            match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
            if match:
                title = match.group(1).strip()
            else:
                match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = match.group(1).strip() if match else slug
            notes.append((slug, title, slug))
    return notes


def get_art_projects(art_dir: Path) -> list[tuple[str, str]]:
    """Get list of art projects. Returns: [(slug, title), ...]"""
    projects = []
    for proj_dir in sorted(art_dir.iterdir()):
        if proj_dir.is_dir() and not proj_dir.name.startswith('_'):
            readme = proj_dir / "README.md"
            if readme.exists():
                content = readme.read_text()
                match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = match.group(1).strip() if match else proj_dir.name
                projects.append((proj_dir.name, title))
    return projects


def publish_daily_notes(daily_dir: Path, published_content: PublishedContent,
                       base_url: str = "https://ashworx-global.github.io/vault"):
    """Publish new or updated daily notes to Patreon and Facebook."""
    for slug, title, _ in get_daily_notes(daily_dir):
        post_url = f"{base_url}/daily/{slug}/"
        
        if published_content.is_published("daily", slug):
            continue
        
        daily_file = daily_dir / f"{slug}.md"
        if not daily_file.exists():
            continue
        
        content = daily_file.read_text()
        if content.startswith("---"):
            _, _, content = content.split("---", 2)
        
        post_content = f"{content}\n\nRead more: {post_url}"
        post_text = strip_html_tags(post_content)[:500]
        
        publish_to_patreon(title, post_content, published_content, "daily", slug)
        publish_to_facebook(title, post_text, post_url, published_content, "daily", slug)


def publish_art_projects(art_dir: Path, published_content: PublishedContent,
                        base_url: str = "https://ashworx-global.github.io/vault"):
    """Publish new or updated art projects to Patreon and Facebook."""
    for slug, title in get_art_projects(art_dir):
        post_url = f"{base_url}/art/{slug}/"
        
        project_dir = art_dir / slug
        readme = project_dir / "README.md"
        exports_dir = project_dir / "exports"
        
        if not readme.exists() or not exports_dir.exists():
            continue
        
        content = readme.read_text()
        images = list(exports_dir.glob("*.png"))
        image_count = len(images)
        
        post_content = f"{content}\n\n🖼️ {image_count} image{'s' if image_count != 1 else ''}\n\nView project: {post_url}"
        post_text = strip_html_tags(post_content)[:500]
        
        publish_to_patreon(f"Art: {title}", post_content, published_content, "art", slug)
        publish_to_facebook(f"Art: {title}", post_text, post_url, published_content, "art", slug)


if __name__ == "__main__":
    REPO = Path(__file__).resolve().parent.parent
    DAILY_DIR = REPO / "Daily"
    ART_DIR = REPO / "Art"
    TRACK_FILE = REPO / ".published-content.json"
    
    print("📱 Publishing to Patreon and Facebook...\n")
    
    published = PublishedContent(TRACK_FILE)
    
    if DAILY_DIR.exists():
        print("📖 Processing daily notes...")
        publish_daily_notes(DAILY_DIR, published)
    
    if ART_DIR.exists():
        print("\n🎨 Processing art projects...")
        publish_art_projects(ART_DIR, published)
    
    print("\n✅ Publishing complete")
