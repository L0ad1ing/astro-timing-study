"""OCR a scanned PDF with Tesseract (English): python ocr_pdf.py <pdf> <out.txt> [workers]. Writes one block per page,
headed '=== PAGE n ===' (n = PDF page). Pages are rendered at ~300 dpi with pypdfium2."""
import subprocess, sys, tempfile, os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import pypdfium2 as pdfium
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def page(args):
    pdf, i, tmp = args
    doc = pdfium.PdfDocument(pdf)
    png = os.path.join(tmp, f"p{i:04d}.png")
    doc[i].render(scale=300 / 72, grayscale=True).to_pil().save(png)
    r = subprocess.run([TESS, png, "-", "-l", "eng", "--psm", "4"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.remove(png)
    return i, r.stdout


if __name__ == "__main__":
    pdf, out = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    n = len(pdfium.PdfDocument(pdf))
    with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor(w) as ex:
        res = dict(ex.map(page, [(pdf, i, tmp) for i in range(n)]))
    Path(out).write_text("".join(f"=== PAGE {i + 1} ===\n{res[i]}\n" for i in range(n)), encoding="utf-8")
    print("pages", n)
