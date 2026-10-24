#!/usr/bin/env python3
"""Asset processor — Convert PSDs to PNG, process logos in multiple sizes.

Reads:
  Art/*/source/       PSD, Krita, or image files
  Art/*/README.md     Journal notes and metadata
  logo/source/        Logo source files

Writes:
  Art/*/exports/      High-res watermarked PNG exports
  logo/exports/       Logo in multiple sizes (favicon, icons, social)
  site/dist/art/      Generated HTML gallery pages

Features:
  - Auto-convert PSD→PNG via ImageMagick
  - Add AI-prevention watermark to art
  - Export logos in multiple sizes (32, 64, 128, 256, 512, 1024, 1200)
  - Organize into lightbox gallery
  - Parse README.md for journal notes
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


def slugify(s: str) -> str:
    """Convert to URL-safe slug."""
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[-\s]+", "-", s).strip("-")


class ArtProject:
    """Represents an art project folder."""

    def __init__(self, folder: Path):
        self.folder = folder
        self.slug = slugify(folder.name)
        self.title = folder.name
        self.source_dir = folder / "source"
        self.export_dir = folder / "exports"
        self.readme = folder / "README.md"
        self.metadata = {"title": self.title, "slug": self.slug, "date": "", "notes": "", "images": []}

    def load_metadata(self) -> None:
        """Parse README.md for frontmatter and notes."""
        if not self.readme.exists():
            return
        
        content = self.readme.read_text(encoding="utf-8", errors="replace")
        
        # Extract frontmatter if present
        fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if fm_match:
            fm_text, notes = fm_match.groups()
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    self.metadata[key.strip().lower()] = val.strip()
            self.metadata["notes"] = notes.strip()
        else:
            # No frontmatter, treat entire content as notes
            # Skip title line if it exists
            lines = content.split("\n")
            if lines and lines[0].startswith("#"):
                self.metadata["notes"] = "\n".join(lines[1:]).strip()
            else:
                self.metadata["notes"] = content.strip()

    def find_source_files(self) -> list[Path]:
        """Find all PSD, Krita, and image files in source/."""
        if not self.source_dir.exists():
            return []
        
        patterns = ("*.psd", "*.psb", "*.kra", "*.xcf", "*.png", "*.jpg", "*.jpeg", "*.tiff")
        files = []
        for pattern in patterns:
            files.extend(self.source_dir.glob(pattern))
        return sorted(files)

    def convert_psd_to_png(self, psd_file: Path, density: int = 300) -> Path | None:
        """Convert PSD to high-res PNG using ImageMagick."""
        output = self.export_dir / f"{psd_file.stem}.png"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use ImageMagick to convert (works with PSD, Krita, etc.)
            cmd = [
                "convert",
                f"{psd_file}[0]",  # First layer only
                "-density", str(density),
                "-background", "white",
                "-alpha", "off",
                str(output)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Converted {psd_file.name} → {output.name}")
            return output
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to convert {psd_file.name}: {e.stderr.decode()}")
            return None

    def watermark_image(self, img_path: Path) -> Path:
        """Add AI-prevention watermark to image."""
        try:
            # Get image dimensions for watermark placement
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.open(img_path)
            width, height = img.size
            
            # Create watermark overlay
            watermark_text = "© Not for AI Training"
            text_color = (255, 255, 255, 102)  # White, ~40% opacity
            
            # Use default font (safer than relying on system fonts)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", max(12, int(height / 30)))
            except:
                font = ImageFont.load_default()
            
            draw = ImageDraw.Draw(img, 'RGBA')
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Place in bottom-right corner with padding
            x = width - text_width - 15
            y = height - text_height - 10
            
            draw.text((x, y), watermark_text, fill=text_color, font=font)
            img.save(img_path)
            print(f"  ✓ Watermarked {img_path.name}")
            return img_path
        except Exception as e:
            print(f"  ⚠ Watermark skipped for {img_path.name} (using PIL failed, image still usable)")
            # Don't fail - image is still valid without watermark
            return img_path

    def process(self) -> bool:
        """Convert sources, watermark, and organize."""
        print(f"\n📸 Processing: {self.title}")
        self.load_metadata()
        
        sources = self.find_source_files()
        if not sources:
            print(f"  ℹ No source files found in {self.source_dir}")
            return True
        
        for src in sources:
            if src.suffix.lower() in (".psd", ".psb", ".kra", ".xcf"):
                # Convert design file to PNG
                exported = self.convert_psd_to_png(src)
                if exported:
                    self.watermark_image(exported)
                    self.metadata["images"].append({"file": exported.name, "source": src.name})
            else:
                # Copy and watermark existing image
                exported = self.export_dir / src.name
                self.export_dir.mkdir(parents=True, exist_ok=True)
                if src != exported:
                    import shutil
                    shutil.copy2(src, exported)
                self.watermark_image(exported)
                self.metadata["images"].append({"file": exported.name, "source": src.name})
        
        return len(self.metadata["images"]) > 0


def process_all_art(art_dir: Path) -> list[ArtProject]:
    """Process all art project folders."""
    projects = []
    
    if not art_dir.exists():
        print("No Art/ folder found.")
        return projects
    
    print("🎨 Processing art galleries...")
    
    for folder in sorted(art_dir.iterdir()):
        if folder.is_dir() and folder.name != "__pycache__":
            project = ArtProject(folder)
            if project.process():
                projects.append(project)
    
    return projects


def generate_gallery_index(projects: list[ArtProject], base_url: str = "/vault") -> str:
    """Generate HTML index for all art projects."""
    if not projects:
        return '<p style="color: #a8a29e;">No art projects yet. Add folders to Art/ to get started.</p>'
    
    cards = []
    for proj in projects:
        if proj.metadata["images"]:
            first_img = proj.metadata["images"][0]["file"]
            card = f'''
    <a href="{base_url}/art/{proj.slug}/" class="card group cursor-pointer hover:border-gold transition">
        <div class="relative w-full h-48 bg-panel rounded mb-3 overflow-hidden">
            <img src="{base_url}/art/{proj.slug}/{first_img}" 
                 alt="{proj.title}" 
                 class="w-full h-full object-cover group-hover:scale-105 transition"
                 style="user-select: none; pointer-events: none;">
        </div>
        <h3 class="font-bold text-lg">{proj.title}</h3>
        <p class="text-sm" style="color: #a8a29e;">{len(proj.metadata["images"])} image{"s" if len(proj.metadata["images"]) != 1 else ""}</p>
    </a>
            '''
            cards.append(card)
    
    return f'<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">{"".join(cards)}</div>'


def process_logos(logo_dir: Path) -> None:
    """Export logo in multiple sizes for web use."""
    source_dir = logo_dir / "source"
    export_dir = logo_dir / "exports"
    
    if not source_dir.exists():
        print("ℹ No logo/source/ folder found")
        return
    
    # Find logo source file (PNG or other format)
    logo_files = list(source_dir.glob("*.png")) + list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.psd"))
    if not logo_files:
        print("ℹ No logo source files found")
        return
    
    source = logo_files[0]  # Use first found logo
    export_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n🎨 Processing logo...")
    
    # Logo sizes: (width, height, name)
    sizes = [
        (32, 32, "favicon-32"),
        (64, 64, "favicon-64"),
        (128, 128, "icon-128"),
        (256, 256, "icon-256"),
        (512, 512, "icon-512"),
        (1024, 1024, "icon-1024"),
        (1200, 630, "social-og"),  # Open Graph / social media
    ]
    
    for width, height, name in sizes:
        output = export_dir / f"{name}.png"
        
        try:
            # Convert and resize
            cmd = [
                "convert",
                f"{source}[0]",  # First layer if PSD
                "-resize", f"{width}x{height}",
                "-background", "white",
                "-gravity", "center",
                "-extent", f"{width}x{height}",
                str(output)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Exported {width}x{height} → {name}.png")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to export {name}: {e.stderr.decode()}")


def copy_logos_to_dist(logo_dir: Path, dist_dir: Path) -> None:
    """Copy exported logos to site/dist for web serving."""
    export_dir = logo_dir / "exports"
    
    if not export_dir.exists():
        return
    
    logos_dist = dist_dir / "logos"
    logos_dist.mkdir(parents=True, exist_ok=True)
    
    import shutil
    for logo_file in export_dir.glob("*.png"):
        dst = logos_dist / logo_file.name
        shutil.copy2(logo_file, dst)


if __name__ == "__main__":
    REPO = Path(__file__).resolve().parent.parent
    ART_DIR = REPO / "Art"
    LOGO_DIR = REPO / "logo"
    
    projects = process_all_art(ART_DIR)
    print(f"\n✅ Processed {len(projects)} art projects")
    
    # Process logos
    process_logos(LOGO_DIR)
