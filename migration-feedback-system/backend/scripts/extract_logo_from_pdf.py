"""
Extract logo/image from 'Migration Feedback Form.pdf' and save to frontend/public/logo.png
for use in the email template.

Run from project root:
  pip install pymupdf
  python backend/scripts/extract_logo_from_pdf.py

If the PDF has no embedded images, add logo.png manually to frontend/public/ (e.g. export from PDF or use your CloudFuze logo).
"""
import sys
from pathlib import Path

# backend/scripts/extract_logo_from_pdf.py -> backend/ -> project root
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
pdf_path = backend_dir / "Migration Feedback Form.pdf"
out_dir = project_root / "frontend" / "public"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "logo.png"


def main():
    try:
        import pymupdf
    except ImportError:
        print("Install pymupdf: pip install pymupdf", file=sys.stderr)
        sys.exit(1)

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    doc = pymupdf.open(pdf_path)
    best_pix = None
    best_size = 0

    for page in doc:
        for img in page.get_images():
            xref = img[0]
            try:
                pix = pymupdf.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                size = pix.width * pix.height
                if size > best_size:
                    best_size = size
                    best_pix = pix
            except Exception:
                continue

    doc.close()

    if best_pix is None:
        print("No images found in PDF. Email will omit logo.", file=sys.stderr)
        sys.exit(0)

    best_pix.save(out_path)
    print(f"Saved logo to {out_path}")


if __name__ == "__main__":
    main()
