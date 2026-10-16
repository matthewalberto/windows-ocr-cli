"""Render only the pages of a PDF that contain given words, so you can read a table as an image.

Usage:
    python find_pages.py <file.pdf> <out_prefix> --match "BALANCE SHEET" --match "FIVE-YEAR" [--ocr <file.ocr.txt>] [--dpi 110]

Why: text extracted from a multi-column table (for example with `pdftotext -layout`) often
shifts figures into the wrong column. Rendering the one or two pages that hold the table and
reading the picture is more reliable.

Matching is case-insensitive. By default it searches the PDF's own text layer. For an
image-only scan, pass --ocr with the text file written by ocr.ps1 (its "===== PAGE nnn ====="
blocks) and pages are matched there instead.

Prints one PNG path per matching page (<out_prefix>_p<n>.png). Exit 1 when nothing matched.
"""
import argparse
import os
import re
import sys

import fitz  # PyMuPDF

PAGE_BLOCK = re.compile(r"===== PAGE (\d+) =====(.*?)(?======|\Z)", re.S)


def ocr_pages(text):
    """Split ocr.ps1 output into {zero_based_page_index: text}."""
    return {int(m.group(1)) - 1: m.group(2) for m in PAGE_BLOCK.finditer(text)}


def matching_pages(texts, needles):
    """Sorted page indexes whose text contains any needle (case-insensitive)."""
    ups = [n.upper() for n in needles]
    return [i for i, body in sorted(texts.items()) if any(n in body.upper() for n in ups)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("out_prefix")
    ap.add_argument("--match", action="append", required=True, help="word or phrase to look for (repeatable)")
    ap.add_argument("--ocr", help="OCR text file from ocr.ps1, for scans with no text layer")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args(argv)

    with fitz.open(a.pdf) as doc:
        if a.ocr:
            with open(a.ocr, encoding="utf-8", errors="replace") as f:
                texts = ocr_pages(f.read())
        else:
            texts = {i: p.get_text() for i, p in enumerate(doc)}
        hits = matching_pages(texts, a.match)
        d = os.path.dirname(a.out_prefix)
        if d:
            os.makedirs(d, exist_ok=True)
        for i in hits:
            fn = f"{a.out_prefix}_p{i + 1}.png"
            doc[i].get_pixmap(dpi=a.dpi).save(fn)
            print(fn)
    if not hits:
        print(f"no page of {os.path.basename(a.pdf)} matched {a.match}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
