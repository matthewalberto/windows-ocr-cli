"""Tests that run anywhere PyMuPDF is installed. They build small synthetic PDFs, so no real
documents are needed."""
import os
import sys
import tempfile
import unittest

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import find_pages  # noqa: E402
from render import render  # noqa: E402


def make_pdf(path, page_texts):
    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 100), text, fontsize=18)
    doc.save(path)
    doc.close()


class RenderTests(unittest.TestCase):
    def test_renders_every_page_and_counts_text_layer(self):
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "sample.pdf")
            make_pdf(pdf, ["Board minutes", "", "Gift agreement"])
            out = os.path.join(td, "pages")
            pages, own = render(pdf, out, dpi=50)
            self.assertEqual(pages, 3)
            self.assertGreater(own, 0)
            self.assertEqual(sorted(os.listdir(out)), ["p001.png", "p002.png", "p003.png"])

    def test_image_only_pdf_has_no_text_layer(self):
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "blank.pdf")
            make_pdf(pdf, ["", ""])
            pages, own = render(pdf, os.path.join(td, "pages"), dpi=50)
            self.assertEqual((pages, own), (2, 0))


class FindPagesTests(unittest.TestCase):
    def test_ocr_text_is_split_into_pages(self):
        text = "===== PAGE 001 =====\nalpha\n===== PAGE 002 =====\nBalance Sheet\n"
        pages = find_pages.ocr_pages(text)
        self.assertEqual(sorted(pages), [0, 1])
        self.assertEqual(find_pages.matching_pages(pages, ["balance sheet"]), [1])

    def test_end_to_end_on_text_layer(self):
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "report.pdf")
            make_pdf(pdf, ["Introduction", "BALANCE SHEET 2025", "Notes"])
            prefix = os.path.join(td, "hits", "report")
            code = find_pages.main([pdf, prefix, "--match", "balance sheet", "--dpi", "40"])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(prefix + "_p2.png"))
            self.assertFalse(os.path.exists(prefix + "_p1.png"))

    def test_no_match_returns_1(self):
        with tempfile.TemporaryDirectory() as td:
            pdf = os.path.join(td, "report.pdf")
            make_pdf(pdf, ["Introduction"])
            code = find_pages.main([pdf, os.path.join(td, "x"), "--match", "nowhere"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
