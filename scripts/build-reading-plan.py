#!/usr/bin/env python3
"""Build a seven-day Markdown resource into A5 PDF, EPUB 3 and page-image CBZ."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
CSS = """
body { font-family: Georgia, serif; line-height: 1.55; color: #222; }
h1, h2 { line-height: 1.2; }
h1 { font-size: 24pt; } h2 { font-size: 15pt; }
a { color: #645019; overflow-wrap: anywhere; }
blockquote { border-left: 3px solid #c8a24a; padding-left: 1em; }
"""
PRINT_CSS = """
@page { size: A5; margin: 17mm;
  @bottom-center { content: counter(page); font-size: 9pt; }
}
body { font-size: 11pt; }
section { break-before: page; }
section:first-child { break-before: auto; }
h1, h2 { break-after: avoid; }
p { orphans: 3; widows: 3; }
"""


def document(title, body, language, style=""):
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" '
        f'lang="{escape(language, quote=True)}">'
        f'<head><title>{escape(title)}</title><meta charset="utf-8"/>'
        f'<style>{CSS}{style}</style></head><body>{body}</body></html>'
    )


def build(source, output, preview):
    import markdown
    from weasyprint import HTML

    metadata = json.loads((source / "book.json").read_text())
    files = [source / "introduction.md"]
    files += [source / f"day-{n:02d}" / "reading.md" for n in range(1, 8)]
    files += [source / "leader-guide.md"]
    texts = [(p, p.read_text(encoding="utf-8")) for p in files]
    if not preview:
        if metadata["status"] != "ready":
            raise ValueError("Book is not ready. Use --preview for draft exports.")
        if not metadata.get("author") or not metadata.get("rights"):
            raise ValueError("Set author and rights before a release build.")
        if any("TODO:" in text for _, text in texts):
            raise ValueError("Complete all TODO: placeholders before release.")
    if not shutil.which("pdftoppm"):
        raise ValueError("CBZ rendering requires pdftoppm (Poppler).")

    title = metadata["title"] + (" — DRAFT PREVIEW" if preview else "")
    language = metadata.get("language", "en")
    chapters = [("Title", f"<h1>{escape(title)}</h1>"
                 f"<p>{escape(metadata.get('subtitle', ''))}</p>"
                 f"<p>{escape(metadata.get('author') or 'Author pending')}</p>"
                 f"<p>{escape(metadata.get('rights', ''))}</p>")]
    for path, text in texts:
        if re.search(r"!\[|\[\[|<\s*(img|script|iframe)\b", text, re.I):
            raise ValueError(f"{path}: use text and standard links; embeds are unsupported.")
        heading = re.search(r"^# (.+)$", text, re.M)
        if not heading:
            raise ValueError(f"{path}: add a level-one chapter heading.")
        body = markdown.markdown(text, extensions=["extra"], output_format="xhtml")
        # EPUB chapters must be well-formed XHTML, including any authored HTML.
        ET.fromstring(document(heading[1], body, language))
        chapters.append((heading[1], body))
    links = []
    for label, url in metadata.get("links", {}).items():
        if not url.startswith("https://"):
            raise ValueError(f"Expected verified HTTPS URL for {label}.")
        links.append(f'<li><a href="{escape(url, quote=True)}">{escape(label)}</a>'
                     f"<br/>{escape(url)}</li>")
    chapters.append(("Continue Reading and Connect",
                     "<h1>Continue Reading and Connect</h1><ul>" + "".join(links) + "</ul>"))
    output.mkdir(parents=True, exist_ok=True)
    stem = "seven-days-in-the-word" + ("-preview" if preview else "")
    # Render everything in a temporary directory so failed builds leave prior exports intact.
    with tempfile.TemporaryDirectory(prefix="reading-plan-", dir=output) as tmp:
        temp = Path(tmp)
        pdf = temp / f"{stem}.pdf"
        body = "".join(f"<section>{body}</section>" for _, body in chapters)
        HTML(string=document(title, body, language, PRINT_CSS)).write_pdf(pdf)
        epub = temp / f"{stem}.epub"
        with ZipFile(epub, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
            archive.writestr("META-INF/container.xml",
                '<?xml version="1.0"?><container version="1.0" '
                'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
                '<rootfile full-path="OEBPS/package.opf" '
                'media-type="application/oebps-package+xml"/></rootfiles></container>')
            manifest, spine, navigation = [], [], []
            for number, (name, content) in enumerate(chapters):
                filename = f"chapter-{number:02d}.xhtml"
                archive.writestr(f"OEBPS/{filename}", document(name, content, language))
                manifest.append(f'<item id="c{number}" href="{filename}" '
                                'media-type="application/xhtml+xml"/>')
                spine.append(f'<itemref idref="c{number}"/>')
                navigation.append(f'<li><a href="{filename}">{escape(name)}</a></li>')
            archive.writestr("OEBPS/nav.xhtml", document("Contents",
                '<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>' +
                "".join(navigation) + "</ol></nav>", language))
            modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            archive.writestr("OEBPS/package.opf",
                '<?xml version="1.0" encoding="utf-8"?>'
                '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
                'unique-identifier="book-id"><metadata '
                'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                f'<dc:identifier id="book-id">{escape(metadata["identifier"])}</dc:identifier>'
                f'<dc:title>{escape(title)}</dc:title><dc:language>{escape(language)}</dc:language>'
                f'<dc:creator>{escape(metadata.get("author") or "Author pending")}</dc:creator>'
                f'<dc:rights>{escape(metadata.get("rights", ""))}</dc:rights>'
                f'<meta property="dcterms:modified">{modified}</meta></metadata><manifest>'
                '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
                + "".join(manifest) + "</manifest><spine>" + "".join(spine) + "</spine></package>")
        subprocess.run(["pdftoppm", "-png", "-r", "150", str(pdf), str(temp / "page")],
                       check=True, capture_output=True)
        pages = sorted(temp.glob("page-*.png"),
                       key=lambda p: int(p.stem.rsplit("-", 1)[1]))
        if not pages:
            raise ValueError("PDF rasterizer produced no pages.")
        with ZipFile(temp / f"{stem}.cbz", "w", compression=ZIP_DEFLATED) as archive:
            for number, page in enumerate(pages, 1):
                archive.write(page, f"page-{number:04d}.png")
        for extension in ("pdf", "epub", "cbz"):
            destination = output / f"{stem}.{extension}"
            shutil.move(temp / destination.name, destination)
            print(destination)
        print(f"Rendered {len(pages)} PDF/CBZ pages and {len(chapters)} EPUB sections.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / "Resources/Seven-Days-in-the-Word")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    try:
        build(args.source, args.out or args.source / "exports", args.preview)
    except (ValueError, FileNotFoundError, ImportError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Build failed: {error}\n")
