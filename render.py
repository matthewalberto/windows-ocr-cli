"""Render every page of a PDF to PNG so it can be OCR'd.

Usage:
    python render.py <file.pdf> <out_dir> [dpi=200]

Writes <out_dir>/p001.png, p002.png, ... and prints the page count and how much text the
PDF already carries in its own text layer. 0 chars means an image-only scan, which is what
this tool is for. Pages that already exist are skipped, so a re-run is cheap.
"""
import os
import sys

import fitz  # PyMuPDF


def text_layer_chars(doc):
    """Characters of selectable text the PDF already has (0 = a pure scan)."""
    return sum(len(page.get_text().strip()) for page in doc)


def render(pdf, out_dir, dpi=200):
    """Render each page to out_dir/pNNN.png. Returns (page_count, text_layer_chars)."""
    os.makedirs(out_dir, exist_ok=True)
    with fitz.open(pdf) as doc:
        own = text_layer_chars(doc)
        for i, page in enumerate(doc):
            png = os.path.join(out_dir, "p%03d.png" % (i + 1))
            if not os.path.exists(png):
                page.get_pixmap(dpi=dpi).save(png)
        return doc.page_count, own


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    pdf, out = argv[0], argv[1]
    dpi = int(argv[2]) if len(argv) > 2 else 200
    pages, own = render(pdf, out, dpi)
    print(f"{os.path.basename(pdf)}: {pages} pages rendered at {dpi} dpi to {out}; "
          f"text layer of its own: {own} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
