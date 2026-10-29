"""PDF safety checks and text extraction with PyMuPDF."""

from __future__ import annotations

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PAGES = 20


class PdfError(ValueError):
    """Raised for any rejected or unreadable PDF; message is safe to show."""


def check_upload(filename: str, content: bytes) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise PdfError("Only .pdf files are accepted.")
    if len(content) == 0:
        raise PdfError("Uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise PdfError("File exceeds the 10 MB limit.")
    if not content.startswith(b"%PDF-"):
        raise PdfError("File does not look like a PDF (missing %PDF- header).")


def extract_text(content: bytes) -> str:
    try:
        import pymupdf as fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - environment error
        raise PdfError("PyMuPDF is not installed. Run: pip install -r requirements.txt") from exc
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        # RC fix (issue 9): never echo the library exception into an API
        # response; it could contain internal detail. Return a generic error.
        raise PdfError("Could not open PDF: file is corrupted or not a valid PDF.") from exc
    try:
        if getattr(doc, "is_encrypted", False):
            # RC fix (issue 1): encrypted PDFs previously raised an unhandled
            # ValueError from get_text() and returned HTTP 500. Reject cleanly.
            raise PdfError("Encrypted PDFs are not supported in v1 (password required).")
        if doc.page_count == 0:
            raise PdfError("PDF has no pages.")
        if doc.page_count > MAX_PAGES:
            raise PdfError(f"PDF has {doc.page_count} pages; v1 supports at most {MAX_PAGES}.")
        try:
            pages = [page.get_text() for page in doc]
        except Exception as exc:
            raise PdfError("Could not read text from PDF.") from exc
    finally:
        doc.close()
    text = "\n".join(pages)
    if not text.strip():
        raise PdfError("No extractable text found in PDF (scanned images are not supported in v1).")
    return text
