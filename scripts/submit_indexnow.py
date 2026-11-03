"""Tell IndexNow (Bing and partners) about every URL in the built sitemap.

Usage: python scripts/submit_indexnow.py [--dist=site/dist] [--dry-run]

Reads the key from indexnow-key.txt in the vault root. The build serves that key
at https://manofgod.online/<key>.txt, which IndexNow uses to verify the site.
Submits the full sitemap each time, so no state is needed between deploys.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOST = "manofgod.online"
ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000


def main() -> int:
    dist = REPO / "site" / "dist"
    dry = False
    for a in sys.argv[1:]:
        if a.startswith("--dist="):
            p = Path(a.split("=", 1)[1])
            dist = p if p.is_absolute() else REPO / p
        elif a == "--dry-run":
            dry = True

    key_file = REPO / "indexnow-key.txt"
    if not key_file.is_file():
        print("indexnow-key.txt not found; nothing to submit")
        return 0
    key = key_file.read_text(encoding="utf-8").strip()
    sitemap = dist / "sitemap.xml"
    if not sitemap.is_file():
        print(f"{sitemap} not found; run the build first")
        return 1

    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text(encoding="utf-8"))
    urls = [u for u in urls if u.startswith(f"https://{HOST}/")]
    print(f"{len(urls)} URLs in sitemap")
    if dry:
        return 0

    key_location = f"https://{HOST}/{key}.txt"
    failed = False
    for i in range(0, len(urls), BATCH):
        body = json.dumps({"host": HOST, "key": key, "keyLocation": key_location,
                           "urlList": urls[i:i + BATCH]}).encode("utf-8")
        req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                print(f"IndexNow accepted batch {i // BATCH + 1}: HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            print(f"IndexNow rejected batch {i // BATCH + 1}: HTTP {e.code} {e.reason}")
            failed = True
        except urllib.error.URLError as e:
            print(f"IndexNow unreachable: {e.reason}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
