"""End-to-end OCR test. Runs only on Windows with an English OCR language installed; skipped
elsewhere. It draws large synthetic text into an image-only PDF, so nothing real is used."""
import os
import subprocess
import sys
import tempfile
import unittest

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import ocr_pdf  # noqa: E402

PHRASE = "WARRANTY DEED RECORDED"


def english_ocr_available():
    if os.name != "nt":
        return False
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        os.path.join(ROOT, "ocr.ps1"), "-ListLanguages"],
                       capture_output=True, text=True)
    return r.returncode == 0 and "en-" in r.stdout


def make_scanned_pdf(path):
    """A PDF whose only page is a picture of text, like a scan: no text layer."""
    src = fitz.open()
    page = src.new_page()
    page.insert_text((60, 120), PHRASE, fontsize=28)
    pix = page.get_pixmap(dpi=200)
    src.close()
    doc = fitz.open()
    img_page = doc.new_page()
    img_page.insert_image(img_page.rect, stream=pix.tobytes("png"))
    doc.save(path)
    doc.close()


@unittest.skipUnless(english_ocr_available(), "needs Windows with an English OCR language pack")
class WindowsOcrTests(unittest.TestCase):
    def test_scanned_pdf_is_read(self):
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "scan.pdf")
            make_scanned_pdf(pdf)
            out = os.path.join(td, "scan.ocr.txt")
            self.assertEqual(ocr_pdf.main([pdf, "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("===== PAGE 001 =====", text)
            self.assertIn("WARRANTY", text.upper())

    def test_image_mode(self):
        with tempfile.TemporaryDirectory() as td:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((60, 120), PHRASE, fontsize=28)
            png = os.path.join(td, "page.png")
            page.get_pixmap(dpi=200).save(png)
            doc.close()
            r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                os.path.join(ROOT, "ocr.ps1"), "-Image", png],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with open(png + ".ocr.txt", encoding="utf-8") as f:
                self.assertIn("DEED", f.read().upper())


if __name__ == "__main__":
    unittest.main()
