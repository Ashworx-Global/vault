---
name: art-exports
description: Use when user says publish art, export PSDs, process art, convert PSD, or update art exports. Scans Art/*/source/ for PSD/Krita/image files and writes watermarked PNGs to Art/*/exports/.
---

# Art Exports — PSD → watermarked PNG

Runs `scripts/art_processor.py` from the vault root. For every `Art/<project>/source/`
it converts `.psd/.psb/.kra/.xcf` to a 300 DPI PNG (ImageMagick, first layer only) and
copies plain images across, then watermarks each result into `Art/<project>/exports/`.

## Steps

1. List what's there: `ls Art/*/source/`. Tell Lee which projects have sources and
   which have none (those are skipped, not errors).
2. Check prerequisites first, they fail quietly:
   - `which magick` (ImageMagick). Missing means every PSD fails.
   - `python3 -c "import PIL"`. Missing means the watermark step is **silently
     skipped** and exports go out unmarked. If it's missing, stop and tell Lee
     (`pip install Pillow` from PyPI; company dependency rules apply) rather
     than publishing unwatermarked art.
3. Run: `python3 scripts/art_processor.py`
4. Read the output. `✗ Failed` lines are conversions that didn't happen; `⚠ Watermark
   skipped` means the PNG is unmarked. Report both plainly.
5. Verify: `ls -l Art/*/exports/` and open one export to eyeball it.

## Gotchas

- This skill is for **local preview only**. `.github/workflows/deploy.yml` already
  installs Pillow + ImageMagick and runs `art_processor.py` then `build-site.py` on
  every push to `main`, so pushing the PSD is all that's needed to publish.
- `Art/*/exports/` is gitignored because CI regenerates it; don't commit exports.
- It reprocesses every project on every run and overwrites existing exports.
- `scripts/build-site.py` reads `Art/*/exports/` to build the gallery pages, but
  doesn't run `art_processor.py` itself. Run the processor first, then
  `python3 scripts/build-site.py` to preview the gallery locally.
- Only the first PSD layer is exported (`[0]`), which is the flattened composite
  for most PSDs saved with "Maximize Compatibility".
- Also processes `logo/source/` into `logo/exports/` when run as a script.
