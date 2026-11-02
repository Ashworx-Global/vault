#!/usr/bin/env python3
"""Keep git in step with Resources/Scripture-Images so the Resources page matches the folder.

The site build reads the folder, but CI builds from git. Images that are on disk and not
staged never reach the deployed site, and images removed from the folder stay on the page
while they are still tracked.

Usage:
  python3 scripts/sync_scripture_images.py           # report only
  python3 scripts/sync_scripture_images.py --apply   # git add new images, git rm --cached stale ones

Files on disk are never deleted or renamed. --apply only changes the git index.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMG_DIR = REPO / "Resources" / "Scripture-Images"
REL = "Resources/Scripture-Images"
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def on_disk() -> set[str]:
    if not IMG_DIR.exists():
        return set()
    return {p.name for p in IMG_DIR.iterdir() if not p.name.startswith(".") and p.suffix.lower() in EXTS}


def tracked() -> set[str]:
    out = git("ls-files", "-z", "--", REL)
    return {Path(p).name for p in out.split("\0") if p and Path(p).suffix.lower() in EXTS}


def key(name: str) -> str:
    # Colons were lost or replaced by a private-use character when files moved between systems,
    # so compare names on letters and digits only to spot the same picture under two names.
    return re.sub(r"[^a-z0-9]", "", Path(name).stem.lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    disk, git_names = on_disk(), tracked()
    new = sorted(disk - git_names)
    stale = sorted(git_names - disk)

    print(f"folder: {len(disk)} images | tracked in git: {len(git_names)}")
    for name in new:
        print(f"  + new (not in git): {name}")
    for name in stale:
        print(f"  - stale (in git, not in folder): {name}")

    tracked_keys = {key(n) for n in git_names}
    same_picture = [n for n in new if key(n) in {key(s) for s in stale}]
    for name in same_picture:
        print(f"  ~ same picture under a different name: {name}")
    dupes = [n for n in new if key(n) in tracked_keys and n not in same_picture]
    for name in dupes:
        print(f"  ? matches a tracked image by name only: {name}")

    if not args.apply:
        print("dry run - rerun with --apply to update the git index")
        return 0

    if stale:
        git("rm", "--cached", "--sparse", "-q", "--ignore-unmatch", "--", *[f"{REL}/{n}" for n in stale])
    if new:
        git("add", "--sparse", "--", *[f"{REL}/{n}" for n in new])
    print(f"applied: staged {len(new)} new, removed {len(stale)} stale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
