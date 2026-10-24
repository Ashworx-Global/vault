#!/usr/bin/env python3
"""Diagnostic script to test Patreon and Facebook API setup."""

import os
import sys

try:
    import requests
except ImportError:
    print("❌ requests library not installed. Run: pip install requests")
    sys.exit(1)


def test_patreon():
    """Test Patreon API connection."""
    token = os.getenv("PATREON_API_TOKEN")
    if not token:
        print("❌ PATREON_API_TOKEN not set")
        return False
    
    print(f"\n🔍 Testing Patreon API...")
    print(f"   Token: {token[:20]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test: Get user identity
    resp = requests.get("https://www.patreon.com/api/oauth2/v2/identity", headers=headers)
    print(f"   /identity endpoint: {resp.status_code}")
    if resp.status_code == 200:
        user = resp.json().get("data", {}).get("attributes", {})
        print(f"   ✓ Authenticated as: {user.get('full_name', 'Unknown')}")
    else:
        print(f"   ✗ Error: {resp.text[:200]}")
        return False
    
    # Test: Get campaigns
    resp = requests.get("https://www.patreon.com/api/oauth2/v2/campaigns", headers=headers)
    print(f"   /campaigns endpoint: {resp.status_code}")
    if resp.status_code == 200:
        campaigns = resp.json().get("data", [])
        if campaigns:
            campaign_id = campaigns[0]["id"]
            print(f"   ✓ Found campaign: {campaign_id}")
            
            # Test: Create a test post (won't actually publish)
            post_data = {
                "data": {
                    "type": "post",
                    "attributes": {
                        "title": "[TEST] Vault Social Publisher",
                        "content": "This is a test post to verify the API is working.",
                        "is_public": False
                    }
                }
            }
            resp = requests.post(
                f"https://www.patreon.com/api/oauth2/v2/campaigns/{campaign_id}/posts",
                json=post_data,
                headers=headers
            )
            print(f"   POST /campaigns/{{id}}/posts: {resp.status_code}")
            if resp.status_code in [200, 201]:
                print(f"   ✓ Successfully created test post!")
                post_id = resp.json().get("data", {}).get("id")
                # Delete it
                requests.delete(
                    f"https://www.patreon.com/api/oauth2/v2/posts/{post_id}",
                    headers=headers
                )
            else:
                print(f"   ✗ Failed to create post: {resp.text[:200]}")
                return False
        else:
            print(f"   ✗ No campaigns found")
            return False
    else:
        print(f"   ✗ Error: {resp.text[:200]}")
        return False
    
    return True


def test_facebook():
    """Test Facebook API connection."""
    token = os.getenv("FACEBOOK_PAGE_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    
    if not token or not page_id:
        print("❌ FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID not set")
        return False
    
    print(f"\n🔍 Testing Facebook API...")
    print(f"   Token: {token[:20]}...")
    print(f"   Page ID: {page_id}")
    
    # Test: Get page info
    resp = requests.get(
        f"https://graph.facebook.com/v18.0/{page_id}",
        params={"access_token": token, "fields": "name,id"}
    )
    print(f"   GET /{page_id}: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Page: {data.get('name', 'Unknown')}")
    else:
        print(f"   ✗ Error: {resp.text[:200]}")
        return False
    
    # Test: Create a test post
    payload = {
        "message": "[TEST] Vault Social Publisher - This is a test post.",
        "access_token": token
    }
    resp = requests.post(
        f"https://graph.facebook.com/v18.0/{page_id}/feed",
        data=payload
    )
    print(f"   POST /{page_id}/feed: {resp.status_code}")
    if resp.status_code in [200, 201]:
        print(f"   ✓ Successfully created test post!")
        post_id = resp.json().get("id")
        # Delete it
        requests.delete(
            f"https://graph.facebook.com/v18.0/{post_id}",
            params={"access_token": token}
        )
    else:
        print(f"   ✗ Failed to create post: {resp.text[:200]}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Social API Setup Diagnostic")
    print("=" * 60)
    
    patreon_ok = test_patreon()
    facebook_ok = test_facebook()
    
    print("\n" + "=" * 60)
    if patreon_ok and facebook_ok:
        print("✅ All systems configured correctly!")
        print("\nYour vault can now publish to Patreon and Facebook.")
    else:
        print("❌ Configuration issues detected")
        if not patreon_ok:
            print("\n🔧 Patreon Fix:")
            print("   1. Go to https://www.patreon.com/settings/apps")
            print("   2. Verify your Personal Use Token is valid")
            print("   3. Update PATREON_API_TOKEN GitHub secret")
        if not facebook_ok:
            print("\n🔧 Facebook Fix:")
            print("   1. Verify your page access token has correct permissions")
            print("   2. Check that FACEBOOK_PAGE_ID is correct (numeric)")
            print("   3. Update both FACEBOOK_PAGE_TOKEN and FACEBOOK_PAGE_ID in GitHub")
    print("=" * 60)
