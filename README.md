# DocFlow AI (English)

中文版：[README_CN.md](README_CN.md)

## Portfolio demo statement (0.1-rc3)

- Author: Haoming Xu; copyright: Copyright (C) 2026 Haoming Xu.
- License: the project code is licensed under GNU AGPL-3.0 only (not or-later); the full text is in
  `LICENSE` (the GNU official text, unmodified). The author's copyright is in this statement and `NOTICE.md`, not in `LICENSE` (the 2007 FSF notice at the top of `LICENSE` belongs to the license document itself). PyMuPDF is used under the AGPL
  path; **no Artifex commercial license has been obtained, and none must be claimed.**
- See `NOTICE.md` for the full third-party license list; the current conclusion is this
  statement and `NOTICE.md`.
- Tests and acceptance: the 91 automated tests in this repository are
  reported in `TEST_REPORT_FINAL.md`. The independent review's
  additional 34 tests (125 in total) are an independent-review conclusion
  reported by the user; they must not be described as re-run here until the
  evidence package is supplied and re-run. Windows Chrome core items and the
  Excel formula sample are independent-review conclusions; browser file
  picker/upload, illegal-file UI prompts, WPS and other items remain
  unexecuted — see the limitations section below and `TEST_REPORT_FINAL.md`.
- Known low-priority UI issue UI-20261029-01: after a successful confirmation,
  an old warning may remain displayed; it does not affect saved or exported
  values. Reproduction details are still to be supplied.
- Browser-attribution correction: the second (RC2) audit did not report a new
  browser policy block — it was unattempted. The first audit's local Chromium
  was blocked on `http://127.0.0.1` with `ERR_BLOCKED_BY_ADMINISTRATOR`;
  the development environment's headless Chrome was blocked by the browser platform policy.
  These must not be conflated.
- This repository is a public portfolio demo; the service itself must still run only on local 127.0.0.1 and must not be exposed to the public internet.

An invoice extraction, validation and human-review system built with Python + FastAPI (version identifier: 0.1-rc3).

**Version identifier:** this package uses `0.1-rc3` everywhere, including `/health`
and the FastAPI version field. The old `1.0.0` is a historical identifier only.

**Positioning:** a portfolio demo, not a production system. Version 1 supports
**one single mock invoice format only**. It does not claim to handle arbitrary
complex documents.

## RC acceptance statements (read first)

- v0.1 is a single-format invoice processing demo system.
- It does not call an LLM by default. The LLM interface is designed only, not
  enabled; `/api/llm` returns `enabled: false`.
- It does not support arbitrary-format PDFs or scanned-image OCR. Scanned PDFs
  and other layouts return missing fields or a clear error, never fabricated results.
- No user authentication is implemented. Do not expose it to the public internet.
  Run only on local `127.0.0.1`; do not serve it with `--host 0.0.0.0`.
- The current project must not be presented as a production-grade SaaS. It has
  no login, permissions, backups, audit logging, high-concurrency or production
  deployment design.

## RC3 fixes (relative to RC2, for the 2026-10-29 second independent audit; see FIXES_RC3.md)

1. Boolean amount (F1): `total_amount: true` was previously converted to 1.0 and
   confirmed/exported. It is now rejected before conversion with a
   `field_validator(mode="before")`, returning 422 with no record change;
   NaN / Infinity amounts still return 400 as before.
2. Malformed grouping (F2): `Total Amount: 1,2,3.45` was silently extracted as
   123.45. Only no-grouping or strict three-digit grouping is now allowed
   (`1240.50` or `1,240.50`); a bad grouping no longer matches, so the amount
   stays None and is flagged missing/format-error, never guessed.
3. Date character range (F3): a full-width year `２０２６-10-29` previously
   confirmed. Dates, invoice numbers and amounts now accept ASCII `[0-9]` only,
   never Unicode `\d`, while the real-calendar check is retained.
4. Abnormal request handling (F4): a bare NaN in a string field previously
   returned 500. A `RequestValidationError` handler now sanitises non-finite
   floats and returns 422 with no record change; NaN / Infinity in the amount
   field still return 400.
5. Inf representation mismatch: a 310-digit amount extracted as inf was stored
   as inf in SQLite while the API showed null. Extraction now converts a
   non-finite amount to None with a warning, and upload applies the same guard
   before insert, so database and API are both None, the record stays pending
   and cannot be confirmed.
6. Upload size scope (corrected): the 10 MB / 413 limit applies only to the
   route's reading stage and the final accept/reject decision. Starlette parses
   multipart first and spools it to a temporary file, so this is not a
   network-level hard limit; a public service would need an entry-level
   request-size limit, which this demo does not have.

## Historical reports

- `SECURITY_CHECK.md`, `TEST_REPORT.md` are frozen v0.1 historical reports;
  `SECURITY_REVIEW_RC.md`, `TEST_REPORT_RC.md` are RC historical reports;
  `FIXES_RC2.md`, `TEST_REPORT_RC2.md` are RC2 historical reports. Each is
  marked at the top as historical and superseded. **Do not cite them as the
  RC3 conclusion.** The current conclusions are in `FIXES_RC3.md`,
  `TEST_REPORT_RC3.md` and `TEST_LOG_RC3.txt`.
- Licensing in this repository follows the author's decision: a GNU
  AGPL-3.0-only `LICENSE` (official text) and a `NOTICE.md` third-party list,
  together with the portfolio demo statement above.
  Licensing in this repository follows the author's decision: GNU AGPL-3.0 only, with the official `LICENSE` text and a `NOTICE.md` third-party list.

## RC2 fixes (relative to RC, for the 2026-10-29 independent audit; see FIXES_RC2.md)

1. Amount bypass (P0): JSON NaN / Infinity previously returned 200 and confirmed,
   with SQLite storing NULL. Now non-finite amounts are rejected before any database
   write: the review endpoint explicitly checks `math.isfinite`, and validation
   marks non-finite amounts as `invalid_amount`, returning 400 with the document
   left unconfirmed and out of exports.
2. Cross-line extraction (P1): a lone `Vendor:` line previously swallowed the next
   line's date as the vendor. Extraction is now line-by-line, with only spaces/tabs
   allowed after a label, never a newline; a blank value stays None and is flagged missing.
3. Blank fields (P1): a vendor of only spaces/tabs previously confirmed. Review now
   strips all string fields first, so blank-after-strip counts as missing and blocks
   confirmation; reasonable length caps were added (vendor 200, invoice number 50).
4. Date format (P2): `2026-1-2` previously confirmed. Now a regex first requires
   exactly `YYYY-MM-DD` (zero-padded), then the calendar check verifies a real date.
5. Acceptance-doc contradictions (P2): MANUAL_ACCEPTANCE.md was rewritten; see the
   corrected status/export rules below.

## Corrected status/export rules

- Invalid review on an **unconfirmed** document: rejected 400, document **stays
  unconfirmed**, not exported.
- Invalid review on an **already confirmed** document: rejected 400, the **old
  confirmed version is retained**, no revocation, no invalid value written, exports
  still show the old value. There is no "unconfirm" transition by design.
- Duplicate invoice numbers are **not a unique constraint**: two documents with
  the same number can both be confirmed and exported; the system only flags a
  warning. The audit report states this is a disclosed product constraint, not an
  unknown vulnerability; a future deduplication policy would be a separate decision.

## RC fixes (relative to frozen v0.1; see SECURITY_REVIEW_RC.md)

1. Encrypted PDFs changed from an unhandled exception (HTTP 500) to a clear 400 rejection.
2. Uploads are now read in chunks; files over 10 MB are rejected while reading,
   instead of loading the whole file into memory first.
3. Review now rejects (400) missing fields, invalid dates/amounts and unsupported
   currencies, leaving the document unconfirmed and out of exports. v0.1 confirmed
   them anyway; this is the most important RC fix.
4. The frontend no longer builds table rows with innerHTML from PDF text; it uses
   textContent throughout, removing the XSS risk from PDF text.
5. CSV export prefixes cells starting with `=`, `+`, `-`, `@`, tab or carriage
   return with a single quote, preventing formula injection.
6. Duplicate invoice numbers are flagged as warnings on upload and review
   (not rejected outright, because re-upload/correction is a legitimate case).
7. Upload filenames are reduced to their basename, and PDF-open failures no longer
   return the library exception text to the API.
8. Dependencies are pinned to the exact versions verified in RC, see `requirements.txt`.

## Features

1. PDF upload with safety checks: `.pdf` only, non-empty, max 10 MB, must start
   with `%PDF-`, max 20 pages.
2. PDF text extraction with PyMuPDF, recording the original filename and status.
3. Extracted fields: invoice number, vendor, invoice date, currency, total amount.
4. Validation: missing fields, invalid dates (e.g. 2026-02-30), amount <= 0,
   abnormal amounts (> 1,000,000), unsupported currencies, invoice-number format.
5. Human review page: correct fields and confirm; confirmed records get
   `review_status = "confirmed"`.
6. SQLite storage for confirmed results and review status.
7. Export: confirmed documents only, in CSV and JSON.
8. Automated tests: 91 tests covering API, extraction, validation and review (see TEST_REPORT_RC3.md).
9. LLM interface: designed only, not wired up. `/api/llm` honestly returns
   `enabled: false, default_method: "rule"`. Rule results are never presented
   as LLM results.

## Install and run (verified on Python 3.12.3)

```bash
cd docflow-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python samples/generate_samples.py
.venv/bin/uvicorn app.main:app --port 8000
```

Open http://127.0.0.1:8000/ and upload a PDF from `samples/`.

## Tests (verified)

```bash
.venv/bin/python -m pytest -v
```

Verified on 2026-10-29 (RC3): **91 passed, 0 failed**, with one unrelated warning
(Starlette TestClient deprecation suggesting httpx2; it does not affect results).
Test files: `tests/test_api.py` (6), `tests/test_extraction.py` (3),
`tests/test_validation.py` (5), `tests/test_rc_acceptance.py` (11),
`tests/test_docflow_independent_regressions.py` (5),
`tests/test_rc2_audit_boundaries.py` (61).
The old figure of 14 was the frozen v0.1 count; RC was 25, RC2 is 30, RC3 is 91.

## Demo data and expected results

All data is fictitious. See `samples/EXPECTED_RESULTS.md`.

| File | Invoice | Vendor | Date | Currency | Total | Expected validation |
|---|---|---|---|---|---|---|
| invoice_001.pdf | INV-2026-001 | Acme Supplies Ltd | 2026-10-15 | USD | 1240.50 | none |
| invoice_002.pdf | INV-2026-002 | Bright Office Co | 2026-10-20 | EUR | 875.00 | none |
| invoice_003.pdf | INV-2026-003 | Northwind Trading | 2026-10-28 | USD | 0.00 | amount must be greater than 0 (correct in review before confirming) |

Live server verification on 2026-10-29: invoice_001 extracted as 1240.5 with no
warnings; invoice_003 extracted as 0.0 with an amount error; correcting 003 to
320.00 and confirming succeeded; CSV/JSON export contained confirmed documents only.

## Architecture

```
static/index.html + style.css + app.js   Frontend: upload, list, review, export
app/main.py                              FastAPI routes: upload/list/detail/review/export/health
app/pdf.py                               PDF safety checks + PyMuPDF text extraction
app/extraction.py                        Deterministic rule extraction (single format)
app/validation.py                        Validation rules
app/database.py                          SQLite (data/docflow.db; tests use a temp DB)
app/llm.py                               LLM interface design (disabled by default, no key, no network call)
samples/generate_samples.py              Generates 3 mock invoice PDFs
tests/                                   pytest tests
```

## Limitations (state these honestly to clients)

- Single invoice format only. A different layout, different field names, or a
  scanned-image PDF will fail or return missing fields; it will never fabricate results.
- No OCR, no FAISS/RAG, no Docker cluster, no cloud deployment, no multi-tenancy.
- No login or permission system. **Do not expose this demo directly to the public
  internet.** Production use requires authentication, authorization, logging and backups.
- SQLite is suitable for demos and small volumes, not for high-concurrency production.
- This repository is a public portfolio demo and does not buy any cloud service.
  The service itself must still run only locally.
  Read `SECURITY_CHECK.md` and `NOTICE.md` before running or publishing.

## Security notes

- No hard-coded secrets, no `.env`, no credentials, no personal information.
- Uploads are checked by extension, `%PDF-` header and PyMuPDF opening; failures
  return a clear error and produce no fabricated result.
- Export is limited to confirmed documents; unconfirmed uploads are never exported.
