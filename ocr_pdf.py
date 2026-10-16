"""OCR a scanned PDF in one step: render its pages, then read them with Windows OCR.

Usage:
    python ocr_pdf.py <file.pdf> [--out <file.ocr.txt>] [--dpi 200] [--language en-US] [--keep-pages <dir>]

Writes <file>.ocr.txt next to the PDF (or to --out), one "===== PAGE nnn =====" block per page.
Page images go to a temporary folder that's deleted afterwards, unless you pass --keep-pages.
Windows only: it calls ocr.ps1, which uses the OCR engine built into Windows 10 and 11.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render import render  # noqa: E402


def run_ocr(data_dir, language):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
           os.path.join(HERE, "ocr.ps1"), "-DataDir", data_dir, "-Language", language]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--out", help="where to write the text (default: <pdf>.ocr.txt beside the PDF)")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--language", default="en-US")
    ap.add_argument("--keep-pages", metavar="DIR", help="keep the page PNGs in this folder")
    a = ap.parse_args(argv)

    if os.name != "nt":
        print("Windows only: this uses the OCR engine built into Windows.", file=sys.stderr)
        return 2
    stem = os.path.splitext(os.path.basename(a.pdf))[0]
    out = a.out or os.path.splitext(a.pdf)[0] + ".ocr.txt"
    work = a.keep_pages or tempfile.mkdtemp(prefix="winocr-")
    try:
        pages, own = render(a.pdf, os.path.join(work, stem), a.dpi)
        print(f"{pages} pages rendered; the PDF's own text layer has {own} chars")
        code = run_ocr(work, a.language)
        if code != 0:
            return code
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        shutil.copyfile(os.path.join(work, stem + ".ocr.txt"), out)
        print(f"text -> {out}")
        return 0
    finally:
        if not a.keep_pages:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
