# windows-ocr-cli

Turn scanned PDFs and images into searchable text on your own Windows PC, using the OCR engine that already ships with Windows 10 and 11.

## Why it matters

- **The problem:** old scanned legal and archive documents often have no text layer, so nobody can search them, and confidential files shouldn't go to a cloud OCR service.
- **What this saves:** searchable text on the machine where the files already are, with no new software to buy or get approved.
- **Where it came from:** built to read scanned legal records in my own research.

Nothing is uploaded. There's no cloud service, no account and no API key, so confidential documents stay on the machine. There's also no OCR package to install: no Tesseract, no OCRmyPDF.

**Windows only.** The OCR step calls `Windows.Media.Ocr` through Windows PowerShell 5.1.

## Who it's for

- **Legal, records and archives staff** with old scans that have no text layer: scanned legal and archive documents. You get a plain text file per document that you can search, quote from and compare.
- **Developers** who need a free, local OCR step in a pipeline and already run on Windows.

## What you need

- Windows 10 or 11
- Python 3.9 or newer
- PyMuPDF, to turn PDF pages into images: `pip install -r requirements.txt`
- An OCR language installed in Windows. English is usually there already. To add another, go to Settings > Time & language > Language & region, add the language and make sure its optional features include OCR.

## Quick start

OCR a whole PDF in one step:

```
python ocr_pdf.py "scan.pdf"
```

That writes `scan.ocr.txt` next to the PDF. Each page starts with a marker like `===== PAGE 001 =====`, so you can cite the page a sentence came from.

Options:

```
python ocr_pdf.py "scan.pdf" --out "text\scan.txt"     # choose where the text goes
python ocr_pdf.py "scan.pdf" --language fr-FR          # use a different installed language
python ocr_pdf.py "scan.pdf" --dpi 300                 # sharper render for small print
python ocr_pdf.py "scan.pdf" --keep-pages pages        # keep the page images to look at later
```

OCR image files (PNG, JPEG, TIFF, BMP, GIF) directly:

```
powershell -NoProfile -ExecutionPolicy Bypass -File ocr.ps1 -Image photo1.jpg,photo2.png
```

Each image gets a `<name>.ocr.txt` beside it, or in `-OutDir` if you give one. A multi-page TIFF only has its first page read; split it first.

See which OCR languages are installed:

```
powershell -NoProfile -ExecutionPolicy Bypass -File ocr.ps1 -ListLanguages
```

## Batch use: many PDFs at once

The one-step script is a wrapper around two tools you can run yourself.

1. Render each PDF's pages to PNG, one folder per document:

   ```
   python render.py "deed-1921.pdf" work\deed-1921 200
   python render.py "minutes-1958.pdf" work\minutes-1958 200
   ```

   It also prints how much text the PDF already has. `0 chars` means it's a pure scan. If the number is large, the PDF already has a text layer and you may not need OCR at all.

2. OCR every folder in one run:

   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File ocr.ps1 -DataDir work
   ```

   This writes `work\deed-1921.ocr.txt`, `work\minutes-1958.ocr.txt` and so on. Re-running `render.py` skips pages that already exist.

## Reading tables: render just the pages you need

Text pulled from a multi-column table (a balance sheet, a five-year summary, a schedule of gifts) often slides figures into the wrong column. It's safer to look at the page itself. `find_pages.py` renders only the pages that contain the words you name:

```
python find_pages.py "annual-report.pdf" tables\report --match "balance sheet" --match "five-year"
```

For a scan with no text layer, point it at the OCR text so it can find the pages:

```
python find_pages.py "annual-report.pdf" tables\report --match "balance sheet" --ocr "annual-report.ocr.txt"
```

It prints one PNG path per matching page and exits with code 1 if nothing matched.

## How accurate is it?

On clean typed scans it's good. Expect the odd one-letter misread on old typefaces, such as "inure" read as "intre". So:

- Before you say a document doesn't contain a phrase, search for a shorter piece of it and look at the page image.
- Don't fix the OCR text by hand. A corrected copy is no longer what the engine read. Keep the OCR output as it is and note the misread separately.
- Handwriting, faint carbon copies and stamps read poorly. Try `--dpi 300` before giving up.
- The engine reads images up to 10,000 pixels on a side. At 200 dpi a normal page is far below that. If you render very large sheets at high dpi, the script warns you.

## Privacy

Everything runs locally. The OCR text of a document can still contain personal details (names, addresses, signatures, account numbers), so treat the `.ocr.txt` files with the same care as the scans. The `.gitignore` here keeps PDFs, images and OCR output out of version control.

## Tests

```
python -m unittest discover -s tests -v
```

The rendering tests run anywhere PyMuPDF installs. The OCR tests only run on Windows with an English OCR language installed, and skip otherwise. All test documents are generated on the fly. The GitHub Actions workflow runs the suite on `windows-latest`.

## License

MIT. See [LICENSE](LICENSE).

---

Built by [Matthew Alberto](https://github.com/matthewalberto). Need a version of this for your team or institution? Get in touch on [LinkedIn](https://www.linkedin.com/in/matthewalberto) or at [matthewalberto.com](https://matthewalberto.com).
