"""RC acceptance tests - independent inputs, NOT reusing samples/generate_samples.py.

Every PDF in this file is built inline with PyMuPDF, with different field
order, missing fields, or broken formats. The tests assert behaviour, not a
hard-coded copy of the generator's output: e.g. a missing vendor must be
reported as missing, and an invalid review must be rejected by the API
(400) and must leave the document unconfirmed and unexported.
"""

import io

import pymupdf as fitz
from fastapi.testclient import TestClient


def _pdf_bytes(lines, encrypt=False):
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 22
    buf = io.BytesIO()
    if encrypt:
        doc.save(buf, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="pw123", owner_pw="owner123")
    else:
        doc.save(buf)
    doc.close()
    return buf.getvalue()


def _client():
    from app.main import app

    return TestClient(app)


def _upload(client, name, data):
    return client.post("/api/upload", files={"file": (name, data, "application/pdf")})


def test_field_order_changed_still_extracts(tmp_db):
    # Vendor first, total before date: regex search must not depend on order.
    pdf = _pdf_bytes([
        "Vendor: Order Matters Ltd",
        "Total Amount: 99.99",
        "Invoice Date: 2026-11-02",
        "Currency: GBP",
        "Invoice Number: INV-2026-777",
    ])
    r = _upload(_client(), "order.pdf", pdf)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["invoice_number"] == "INV-2026-777"
    assert d["vendor"] == "Order Matters Ltd"
    assert d["total_amount"] == 99.99
    assert d["warnings"] == []


def test_missing_vendor_flagged_and_blocks_confirmation(tmp_db):
    client = _client()
    pdf = _pdf_bytes([
        "Invoice Number: INV-2026-778",
        "Invoice Date: 2026-11-02",
        "Currency: USD",
        "Total Amount: 10.00",
    ])
    d = _upload(client, "missing.pdf", pdf).json()
    assert any("vendor" in w for w in d["warnings"])
    r = client.post(f"/api/documents/{d['id']}/review", json={
        "invoice_number": "INV-2026-778", "vendor": None,
        "invoice_date": "2026-11-02", "currency": "USD", "total_amount": 10.00,
    })
    assert r.status_code == 400
    after = client.get(f"/api/documents/{d['id']}").json()
    assert after["review_status"] != "confirmed"
    assert "INV-2026-778" not in client.get("/api/export?format=csv").text


def test_invalid_date_and_amount_format(tmp_db):
    client = _client()
    # 2026-02-30 is not a real date; "abc" is not a parseable total.
    pdf = _pdf_bytes([
        "Invoice Number: INV-2026-779",
        "Vendor: Bad Format Co",
        "Invoice Date: 2026-02-30",
        "Currency: USD",
        "Total Amount: abc",
    ])
    d = _upload(client, "bad.pdf", pdf).json()
    assert any("invalid_date" in w for w in d["warnings"])
    assert any("total_amount" in w for w in d["warnings"])
    assert d["total_amount"] is None


def test_duplicate_invoice_number_flagged(tmp_db):
    client = _client()
    lines = [
        "Invoice Number: INV-2026-780",
        "Vendor: Dup Co",
        "Invoice Date: 2026-11-03",
        "Currency: USD",
        "Total Amount: 5.00",
    ]
    first = _upload(client, "a.pdf", _pdf_bytes(lines)).json()
    second = _upload(client, "b.pdf", _pdf_bytes(lines)).json()
    assert first["id"] != second["id"]
    assert any("duplicate_invoice_number" in w for w in second["warnings"])


def test_illegal_empty_and_corrupt_pdf_rejected(tmp_db):
    client = _client()
    assert _upload(client, "note.txt", b"hello").status_code == 400
    assert _upload(client, "empty.pdf", b"").status_code == 400
    assert _upload(client, "fake.pdf", b"not a pdf at all").status_code == 400
    valid = _pdf_bytes(["Invoice Number: INV-2026-781"])
    corrupt = valid[:100]  # truncated file: header present, body broken
    assert _upload(client, "corrupt.pdf", corrupt).status_code == 400


def test_encrypted_pdf_rejected_with_400_not_500(tmp_db):
    client = _client()
    pdf = _pdf_bytes(["Invoice Number: INV-2026-782"], encrypt=True)
    r = _upload(client, "encrypted.pdf", pdf)
    assert r.status_code == 400
    assert "Encrypted" in r.json()["detail"]


def test_export_without_review_excludes_document(tmp_db):
    client = _client()
    pdf = _pdf_bytes([
        "Invoice Number: INV-2026-783",
        "Vendor: Not Reviewed Ltd",
        "Invoice Date: 2026-11-04",
        "Currency: USD",
        "Total Amount: 42.00",
    ])
    _upload(client, "pending.pdf", pdf)
    assert "INV-2026-783" not in client.get("/api/export?format=csv").text
    assert "INV-2026-783" not in client.get("/api/export?format=json").text


def test_api_cannot_confirm_invalid_amount(tmp_db):
    client = _client()
    pdf = _pdf_bytes([
        "Invoice Number: INV-2026-784",
        "Vendor: Zero Co",
        "Invoice Date: 2026-11-05",
        "Currency: USD",
        "Total Amount: 10.00",
    ])
    d = _upload(client, "zero.pdf", pdf).json()
    for bad_total in (0, -5):
        r = client.post(f"/api/documents/{d['id']}/review", json={
            "invoice_number": "INV-2026-784", "vendor": "Zero Co",
            "invoice_date": "2026-11-05", "currency": "USD", "total_amount": bad_total,
        })
        assert r.status_code == 400, (bad_total, r.text)
    after = client.get(f"/api/documents/{d['id']}").json()
    assert after["review_status"] != "confirmed"
    assert "INV-2026-784" not in client.get("/api/export?format=csv").text


def test_csv_formula_injection_neutralised(tmp_db):
    client = _client()
    pdf = _pdf_bytes([
        "Invoice Number: INV-2026-785",
        "Vendor: =2+2",
        "Invoice Date: 2026-11-06",
        "Currency: USD",
        "Total Amount: 10.00",
    ])
    d = _upload(client, "formula.pdf", pdf).json()
    r = client.post(f"/api/documents/{d['id']}/review", json={
        "invoice_number": "INV-2026-785", "vendor": "=2+2",
        "invoice_date": "2026-11-06", "currency": "USD", "total_amount": 10.00,
    })
    assert r.status_code == 200
    csv_text = client.get("/api/export?format=csv").text
    # The vendor cell must not start a formula in a spreadsheet.
    assert "'=2+2" in csv_text
    assert "\n=2+2" not in csv_text and ",=2+2" not in csv_text


def test_frontend_does_not_use_innerhtml_for_untrusted_data():
    # The risk is an assignment that parses untrusted PDF text as HTML.
    # Mentions of the word in comments are not assignments and are ignored.
    from pathlib import Path

    js = Path(__file__).resolve().parent.parent.joinpath("static", "app.js").read_text()
    assert "innerHTML =" not in js
    assert "innerHTML +=" not in js
    assert "textContent" in js


def test_oversized_upload_rejected(tmp_db):
    client = _client()
    # 10 MB + 1 byte, header looks like a PDF but size alone must reject it.
    big = b"%PDF-1.4\n" + b"0" * (10 * 1024 * 1024)
    r = _upload(client, "big.pdf", big)
    assert r.status_code in (400, 413)
