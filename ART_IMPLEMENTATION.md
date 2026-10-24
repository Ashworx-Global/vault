# 🎨 Art Gallery Implementation Summary

Your markdown-driven site now has a complete art gallery system with automatic PSD conversion, watermarking, AI protection, and a modern lightbox interface.

## ✅ What's Been Set Up

### 1. **Folder Structure** (`Art/`)
```
Art/
├── README.md           # Overview + quick start
├── SETUP.md           # Comprehensive setup guide
├── sample-study-01/   # Example project
│   ├── README.md      # Process notes (journal-style)
│   ├── source/        # PSD/Krita files (local only)
│   └── exports/       # High-res watermarked PNGs
└── [your projects]/
```

### 2. **Features Implemented**

#### 🔄 Auto-Conversion
- **Input**: PSD, Krita (.kra), XCF files in `source/` folder
- **Output**: High-resolution PNG at 300 DPI
- **Tool**: ImageMagick (already installed on your Mac)
- **Automation**: Runs automatically when you `python3 scripts/build-site.py`

#### 🔒 AI Protection (Two-Layer)
**Layer 1: Watermark**
- Text: `© Not for AI Training • Original Art`
- Applied to every image automatically
- Bottom-right corner, semi-transparent white
- Visible disclaimer that images aren't for training data

**Layer 2: Right-Click Prevention**
- Users **cannot** right-click → save image
- Also prevents drag-drop saving
- Implemented via JavaScript (passive — can be bypassed by tech-savvy users, but discourages casual copying)

#### 🖼️ Modern Gallery View
- **Index Page** (`/art/`): Grid of all projects (responsive 2-3 columns)
- **Project Page** (`/art/project-name/`): Individual gallery
- **Lightbox Interface**:
  - Click image to enlarge
  - ← → buttons or arrow keys to navigate
  - ESC or click outside to close
  - Full-size viewing (no compression)

#### 📝 Journal/Process Notes
- Each project has a `README.md`
- Write in Markdown (supports headings, lists, bold, italics, etc.)
- Rendered as HTML below the gallery
- Perfect for documenting:
  - What you were exploring
  - Design decisions
  - Iterations and learnings
  - Process notes and reflections

### 3. **Build Integration**

#### Modified Files
- ✅ `scripts/build-site.py` — Added art gallery processing
- ✅ Navigation header — Added "Art" link
- ✅ Navigation footer — Added "Art" link
- ✅ CSS/JS — Lightbox + right-click protection

#### New Files
- ✅ `scripts/art_processor.py` — PSD converter, watermarker, organizer
- ✅ `Art/` folder structure with README and setup guide
- ✅ `Art/sample-study-01/` — Working example

#### Build Command (No Changes Needed!)
```bash
python3 scripts/build-site.py
```

The art processing happens automatically during the build:
1. Scans `Art/` for project folders
2. Finds PSDs in `source/` and converts to PNG
3. Watermarks all images
4. Reads README.md for project notes
5. Generates HTML pages with lightbox
6. Copies everything to `site/dist/art/`

## 🚀 Getting Started

### Create Your First Art Project

```bash
# Navigate to vault
cd /Users/lee-roy.ashworth/Ashworx/vault

# Create project structure
mkdir -p Art/my-first-study/source Art/my-first-study/exports

# Create process notes
cat > Art/my-first-study/README.md << 'EOF'
# My First Study

## What I Was Exploring

- Color harmony and composition
- Typography integration
- Negative space principles

## Process

Started with pencil sketches, moved to digital, experimented with 3 color palettes.

## Key Learnings

- Complementary colors create visual tension
- White space guides the viewer's eye
EOF

# Export your design as PNG from Photoshop/Krita
# Place in: Art/my-first-study/exports/design-01.png
# OR put PSDs in source/ for auto-conversion:
# cp /path/to/your-design.psd Art/my-first-study/source/

# Build the site
python3 scripts/build-site.py

# Verify it worked
open site/dist/art/my-first-study/index.html

# Stage and push to GitHub
git add Art/
git commit -m "Add my first study"
git push origin main

# View on the web in 2-3 minutes
# https://ashworx-global.github.io/vault/art/
```

## 📊 How Watermarking Works

```
Your PSD/Image
    ↓
ImageMagick conversion (if PSD)
    ↓
Add watermark overlay
    ↓
Save high-res PNG to exports/
    ↓
Copy to site/dist/art/
    ↓
Publish to GitHub Pages
```

**Result**: Every image on the web has the watermark automatically applied.

**Customization**: Edit `scripts/art_processor.py` line ~110 to change the watermark text.

## 🔐 Right-Click Protection Implementation

JavaScript disables:
- ❌ Right-click → Save image
- ❌ Drag-drop saving
- ✅ Viewing (full screen, lightbox)
- ✅ Copying image URL

The protection is applied to:
- All images in the gallery (`data-lightbox` attribute)
- Lightbox preview images (`data-no-save` attribute)

## 📁 File Organization Best Practices

### Good Structure
```
Art/
├── color-studies/
├── typography-explorations/
├── ui-design-mockups/
└── character-sketches/
```

### Scale Up (Many Projects)
```
Art/
├── 2026-09/
│   ├── study-01/
│   └── study-02/
├── 2026-10/
│   ├── investigation-01/
│   └── investigation-02/
└── archive/
    └── early-work/
```

Build script recursively finds all projects.

## ⚙️ Configuration Options

All in `scripts/art_processor.py`:

**Change watermark text** (line ~110):
```python
watermark_text = "© Your Name • Not for AI Training"
```

**Change export resolution** (line ~87):
```python
"-density", "300",  # 150 for fast, 600 for ultra-high-res
```

**Disable watermark** (lines 93-103):
```python
# Comment out: self.watermark_image(exported)
```

## 🎯 Typical Workflow

```
Design in Photoshop/Krita
    ↓
Export to: Art/project-name/source/design.psd
    ↓
Write process notes in: Art/project-name/README.md
    ↓
Run: python3 scripts/build-site.py
    ↓
Check locally: open site/dist/art/project-name/index.html
    ↓
Push: git add Art/ && git commit && git push
    ↓
View on web (2-3 min): https://ashworx-global.github.io/vault/art/
```

## 🔍 Verification Checklist

- ✅ `Art/` folder created with README and SETUP.md
- ✅ `scripts/art_processor.py` created (PSD conversion + watermarking)
- ✅ `scripts/build-site.py` modified (art processing integrated)
- ✅ Navigation updated ("Art" link in header + footer)
- ✅ Lightbox CSS + JavaScript added
- ✅ Right-click protection implemented
- ✅ Sample project created at `Art/sample-study-01/`
- ✅ Build tested successfully (builds 236 pages including art galleries)
- ✅ Art gallery pages generated at `site/dist/art/`

## 📚 Documentation Files

- **`Art/README.md`** — Project overview + quick start
- **`Art/SETUP.md`** — Comprehensive setup and troubleshooting guide
- **`Art/sample-study-01/`** — Working example project

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| PSDs not converting | Check ImageMagick: `which convert` |
| Images not appearing | Verify `exports/` folder has PNG files |
| Watermark missing | Restart build: `python3 scripts/build-site.py` |
| Site not updating | Hard-refresh browser: `Cmd+Shift+R` (Mac) |
| Build fails | Check syntax: `python3 -m py_compile scripts/build-site.py` |

## 🎨 Tips & Tricks

- **Batch projects**: Add multiple projects, one `build-site.py` run processes them all
- **Keep sources**: PSDs in `source/` stay local, can re-export anytime
- **Revision workflow**: Overwrite exports with new versions, build re-publishes
- **Naming**: Use descriptive folder names: `color-study-02`, not `new_project`
- **Watermark text**: Keep short so it fits images nicely
- **Image formats**: PNG recommended (lossless), JPG works too

## 📱 What's Published to GitHub Pages

| Item | Published | Privacy |
|------|-----------|---------|
| `Art/*/README.md` | ✅ HTML | Public |
| `Art/*/exports/` | ✅ Images | Public (watermarked) |
| `Art/*/source/` | ❌ No | Private (local only) |
| Watermark | ✅ Yes | Always applied |

## 🎬 Next Steps

1. **Read** `Art/SETUP.md` for full documentation
2. **Delete** `Art/sample-study-01/` when you're ready
3. **Create** your first project folder
4. **Export** high-res images (or PSD files)
5. **Write** process notes in README.md
6. **Build** and push to GitHub
7. **Share** your work!

---

**Questions?** Check the SETUP.md guide for detailed troubleshooting and configuration options.

Happy creating! 🎨✨
