# Art Gallery Setup Guide

Your markdown-driven site now includes a fully-featured art gallery system. Here's how to use it.

## 📁 Folder Structure

```
Art/
├── README.md                      (This file)
├── sample-study-01/               (Example project)
│   ├── README.md                  (Journal/process notes)
│   ├── source/                    (PSD, Krita, XCF files — not published)
│   │   └── design.psd
│   └── exports/                   (Auto-converted or manually exported PNGs)
│       └── image-01.png
│
└── your-project-name/
    ├── README.md                  (Your notes)
    ├── source/                    (Design files)
    └── exports/                   (High-res images)
```

## 🎨 Creating a New Art Project

1. **Create folder**: `Art/your-project-name/`
2. **Create subfolders**: `source/` and `exports/`
3. **Add README.md**: Document your process, thoughts, what you were exploring
4. **Add images**: Put PSD/Krita files in `source/` OR directly in `exports/`

### Example README.md

```markdown
# My Design Exploration

## What I was trying

- Exploring color harmony in abstract shapes
- Testing negative space principles
- Investigating typography + image relationships

## Process

Started with initial sketches, evolved through 5 iterations.

## Key learnings

- Complementary colors create visual tension (good!)
- White space guides the eye
- Less is often more

---

Add process notes, journal entries, or any reflection here.
```

## 🖼️ Adding Images

### Option A: Auto-Convert PSDs (Recommended)

```bash
# Put PSD/Krita/XCF files in source/
Art/my-project/source/design.psd
Art/my-project/source/sketch.kra
```

**When you run `python3 scripts/build-site.py`:**
- ✅ Automatically converts to high-res PNG (300 DPI)
- ✅ Adds AI-prevention watermark
- ✅ Places in `exports/` folder
- ✅ Publishes to website

### Option B: Manual Export

1. Export your design as high-res PNG from Photoshop/Krita (300+ DPI recommended)
2. Place in `Art/your-project/exports/`
3. Watermark is added automatically during build

### Image Naming

- Use descriptive names: `gradient-study-01.png`, `typography-test.png`
- Avoid special characters
- Numbered sequences work well: `exploration-01.png`, `exploration-02.png`

## 🔒 Security Features

### Right-Click Protection
- Users **cannot** right-click → save image on the website
- Also prevents drag-drop saving
- This is **passive** — tech-savvy users can bypass it, but it discourages casual copying

### Watermark
- **Automatic** watermark: `© Not for AI Training • Original Art`
- Added to every exported image during build
- Configurable in `art_processor.py` if you want to change the text

### Why Both?
- **Watermark** = Visual declaration + technical metadata
- **Right-click disable** = Friction to discourage AI scraping
- **Together** = Clear message: "This is original art, not for training"

## 🎬 Lightbox Gallery View

When you browse the site:

- **Grid view**: Thumbnails of all images in a project
- **Click image**: Opens full-screen lightbox
- **Navigate**: Use ← → buttons or arrow keys
- **Close**: Press ESC, click X, or click outside image
- **Full size**: Images are high-res, locked at natural size (no downsampling)

## 🔄 Build Process

```bash
cd /Users/lee-roy.ashworth/Ashworx/vault
python3 scripts/build-site.py
```

The build will:

1. ✅ Find all folders in `Art/`
2. ✅ Read each `README.md` for journal notes
3. ✅ Convert PSDs in `source/` to PNG
4. ✅ Watermark all images
5. ✅ Copy to `site/dist/art/` for publishing
6. ✅ Generate gallery pages with lightbox

**Time**: Usually ~10-30 seconds depending on file sizes

## 📝 Folder Structure Best Practices

### Good Structure
```
Art/
├── color-study-01/
├── typography-experiments/
├── ui-mockup-exploration/
└── character-design-sketches/
```

All your images + notes together, easy to organize by theme or project.

### Managing Large Libraries

If you accumulate many projects:

```
Art/
├── 2026-09/
│   ├── study-01/
│   └── study-02/
├── 2026-10/
│   ├── investigation-alpha/
│   └── investigation-beta/
└── archive/
    └── early-experiments/
```

The build script will recursively find all projects.

## ⚙️ Configuration

### Watermark Text

Edit `scripts/art_processor.py` line ~110:

```python
watermark_text = "© Your Name • Not for AI Training"
```

### Export Resolution

Edit `scripts/art_processor.py` line ~87, change `density`:

```python
subprocess.run([
    "convert",
    f"{psd_file}[0]",
    "-density", "300",  # Change 300 to 150 (faster) or 600 (higher quality)
    ...
])
```

### Disable Watermark

Comment out the watermark section in `art_processor.py` (lines 93-103).

## 🚀 Publishing to GitHub Pages

The site builds automatically on every push to `main`:

```bash
# Stage your changes
git add Art/

# Commit with meaningful message
git commit -m "Add color study 01 and typography exploration"

# Push to GitHub (build runs automatically)
git push origin main
```

The gallery will appear at:
```
https://ashworx-global.github.io/vault/art/
```

## 📊 What Gets Published

| Item | Published? | Notes |
|------|-----------|-------|
| `Art/*/README.md` | ✅ Yes | Converted to HTML, shown on project page |
| `Art/*/exports/*.png` | ✅ Yes | High-res images with watermark |
| `Art/*/source/*` | ❌ No | Local-only (PSDs never published) |
| Watermark | ✅ Yes | Always applied during build |

## 🎯 Typical Workflow

```
1. Design in Photoshop/Krita
   └─ Save as PSD in Art/project/source/

2. Write process notes
   └─ Update Art/project/README.md

3. Run build locally (optional preview)
   └─ python3 scripts/build-site.py

4. Push to GitHub
   └─ git add Art/ && git commit && git push

5. Check website
   └─ https://ashworx-global.github.io/vault/art/your-project/

6. Done! ✨
```

## 🆘 Troubleshooting

### PSDs not converting
- Make sure ImageMagick is installed: `which convert`
- Check file sizes (very large files may fail)
- Verify `Art/project/source/` and `Art/project/exports/` exist

### Images not appearing
- Check that export folder has `.png` files (not `.jpg` yet)
- Verify file names don't have spaces or special characters
- Run build again: `python3 scripts/build-site.py`

### Watermark text is cut off
- Shorten the watermark text in `art_processor.py`
- Or increase image width to accommodate longer text

### Site not updating
- Hard-refresh browser: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Windows/Linux)
- GitHub Actions build may take 2-3 minutes
- Check repo settings → Pages → source is set to "Deploy from a branch" → main

## 💡 Tips

- **Date folders**: Use `2026-10-24-study-name/` for chronological organization
- **Watermark placement**: It goes bottom-right, works well for portraits and landscapes
- **Image formats**: PNG recommended (lossless, preserves quality)
- **Batch processing**: Process multiple files in `source/` — build handles them all
- **Revisiting work**: Keep `source/` files forever; easy to re-export if needed

## 📚 Files Modified

This feature added/modified:

- ✅ Created: `Art/` folder structure
- ✅ Created: `scripts/art_processor.py` (PSD converter + watermarker)
- ✅ Modified: `scripts/build-site.py` (added art gallery integration)
- ✅ Added to navigation: "Art" link in header + footer
- ✅ Added: Lightbox CSS + JavaScript for gallery
- ✅ Added: Right-click protection on images

---

**Questions?** Check the sample project at `Art/sample-study-01/` for a working example.

Happy creating! 🎨
