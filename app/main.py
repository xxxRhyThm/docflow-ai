"""DocFlow AI - FastAPI application (version 0.1-rc3, single invoice format).

Run locally:
    uvicorn app.main:app --reload --port 8000
Then open http://127.0.0.1:8000/
"""

from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

APP_VERSION = "0.1-rc3"

from . import database
from .extraction import extract_invoice_fields
from .llm import describe_llm_interface
from .pdf import MAX_FILE_SIZE_BYTES, PdfError, check_upload, extract_text
from .validation import blocking_errors, validate_invoice


def _safe_filename(filename: str) -> str:
    """Strip any directory components from a client-supplied filename (RC, issue 9)."""
    name = Path(filename or "").name.strip()
    return name if name else "unknown.pdf"


async def _read_upload_limited(file: UploadFile) -> bytes:
    """Read at most MAX_FILE_SIZE_BYTES + 1 byte, in chunks (RC, issue 2).

    RC3 scope correction (audit §4.1): this limit applies ONLY to the bytes
    the route itself holds in memory and to the final accept/reject decision
    (413 over the limit). It is NOT a network-level hard limit: Starlette
    parses the multipart body first and spools it to a temporary file, so an
    over-limit upload has already been received and spooled before this
    function runs. It also does not cap CPU used by PDF parsing. A public
    service would need an entry-level request-size limit (reverse proxy or
    middleware) in addition to this check; this demo has none.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit.")
        chunks.append(chunk)
    return b"".join(chunks)


def _csv_safe(value) -> object:
    """Neutralise CSV formula injection (RC, issue 7).

    Values starting with =, +, -, @, tab or carriage return are prefixed with
    a single quote so spreadsheet programs treat them as text, not formulas.
    Non-string values pass through unchanged.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="DocFlow AI", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _sanitize_for_json(value):
    """Make a value safe for strict JSON serialisation (RC3, audit F4).

    Starlette's JSONResponse refuses non-finite floats, so a validation
    error whose 'input' is a bare JSON NaN used to turn into HTTP 500 when
    the error handler tried to render it. Non-finite floats become their
    string form; any other non-JSON type becomes str(value).
    """
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _sanitize_for_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_json(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request, exc: RequestValidationError):
    # RC3 fix (audit F4): return a client error (422), never 500, for a
    # request that fails Pydantic validation -- including a bare NaN in a
    # string field. No database write happens on this path.
    return JSONResponse(status_code=422, content={"detail": _sanitize_for_json(exc.errors())})


class ReviewRequest(BaseModel):
    invoice_number: str | None = None
    vendor: str | None = None
    invoice_date: str | None = None
    currency: str | None = None
    total_amount: float | None = None

    @field_validator("total_amount", mode="before")
    @classmethod
    def _reject_boolean_amount(cls, value):
        # RC3 fix (audit F1): reject bool BEFORE Pydantic converts it.
        # bool is a subclass of int, so float(True) == 1.0 otherwise.
        # This returns 422, which the audit test accepts (400/422), and no
        # record is written. NaN/Infinity are deliberately NOT rejected
        # here: they pass through to the review() finite gate, which
        # returns the established 400 for those cases.
        if isinstance(value, bool):
            raise ValueError("total_amount must be a number, not a boolean")
        return value


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "DocFlow AI", "version": APP_VERSION}


@app.get("/api/llm")
def llm_status() -> dict:
    """Honest status: LLM extraction is designed but NOT wired up in v1."""
    return describe_llm_interface()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    content = await _read_upload_limited(file)
    safe_name = _safe_filename(file.filename or "")
    try:
        check_upload(safe_name, content)
        text = extract_text(content)
    except PdfError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    extracted = extract_invoice_fields(text)
    fields = {
        "invoice_number": extracted.invoice_number,
        "vendor": extracted.vendor,
        "invoice_date": extracted.invoice_date,
        "currency": extracted.currency,
        "total_amount": extracted.total_amount,
    }
    # RC3 defence in depth (audit §4.2): even if extraction ever returned a
    # non-finite amount again, it must never reach the database, where it
    # would be stored as inf while the API shows null. Extraction already
    # converts inf to None; this guard makes the invariant hold here too.
    if isinstance(fields["total_amount"], float) and not math.isfinite(fields["total_amount"]):
        fields["total_amount"] = None
    warnings = list(extracted.warnings) + validate_invoice(fields)
    # RC fix (issue 8): duplicate invoice numbers are flagged, not silently
    # accepted and not rejected outright (a re-upload/correction is legitimate).
    if fields["invoice_number"]:
        dupes = database.find_duplicate_invoice_numbers(fields["invoice_number"])
        if dupes:
            warnings.append(
                f"duplicate_invoice_number: invoice_number already exists in document(s) {dupes}"
            )
    record = database.insert_document(safe_name, fields, warnings)
    return record


@app.get("/api/documents")
def documents() -> list[dict]:
    return database.list_documents()


@app.get("/api/documents/{doc_id}")
def document(doc_id: int) -> dict:
    record = database.get_document(doc_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return record


@app.post("/api/documents/{doc_id}/review")
def review(doc_id: int, payload: ReviewRequest) -> dict:
    existing = database.get_document(doc_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    # RC2 fix (audit P1): strip all string fields before validation/storage,
    # so " \t " becomes missing instead of a stored vendor value, and
    # surrounding spaces never reach the database.
    fields = payload.model_dump()
    for key in ("invoice_number", "vendor", "invoice_date", "currency"):
        if isinstance(fields.get(key), str):
            fields[key] = fields[key].strip() or None
    # RC2 fix (audit P0): explicit finite gate BEFORE any database write.
    # Pydantic accepts JSON NaN/Infinity as floats, and validate_invoice
    # alone used to let NaN through (all comparisons False) and Infinity
    # through as a mere warning, with SQLite storing NaN as NULL. This gate
    # and the validation fix below both block it; neither is relied on alone.
    total = fields.get("total_amount")
    if total is not None and isinstance(total, float) and not math.isfinite(total):
        raise HTTPException(status_code=400, detail="invalid_amount: total_amount must be a finite number")
    warnings = validate_invoice(fields)
    # RC fix (issues 3/4): v0.1 re-validated on review but still marked the
    # document confirmed even with missing/invalid fields, so a direct API
    # call could bypass validation. Now blocking errors reject the review
    # and leave the document unconfirmed. Re-reviewing an already-confirmed
    # document is allowed as a correction, but it is re-validated the same way.
    errors = blocking_errors(warnings)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    if fields["invoice_number"]:
        dupes = database.find_duplicate_invoice_numbers(fields["invoice_number"], exclude_id=doc_id)
        if dupes:
            warnings.append(
                f"duplicate_invoice_number: invoice_number already exists in document(s) {dupes}"
            )
    return database.update_review(doc_id, fields, warnings)


@app.get("/api/export")
def export(format: str = "json") -> Response:
    """Export CONFIRMED documents only. Unconfirmed uploads are not exported."""
    confirmed = [d for d in database.list_documents() if d["review_status"] == "confirmed"]
    if format == "json":
        body = json.dumps(confirmed, ensure_ascii=False, indent=2)
        return Response(content=body, media_type="application/json",
                        headers={"Content-Disposition": "attachment; filename=docflow-confirmed.json"})
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "original_filename", "invoice_number", "vendor",
                         "invoice_date", "currency", "total_amount", "review_status"])
        for d in confirmed:
            writer.writerow([_csv_safe(v) for v in
                             [d["id"], d["original_filename"], d["invoice_number"], d["vendor"],
                              d["invoice_date"], d["currency"], d["total_amount"], d["review_status"]]])
        return Response(content=buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=docflow-confirmed.csv"})
    raise HTTPException(status_code=400, detail="format must be 'json' or 'csv'.")
