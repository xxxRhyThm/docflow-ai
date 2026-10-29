import io

import pymupdf as fitz  # PyMuPDF (avoids deprecated fitz import warning)
from fastapi.testclient import TestClient


def _make_pdf_bytes(lines):
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 22
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _client():
    from app.main import app

    return TestClient(app)


def test_health(tmp_db):
    r = _client().get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_extract_and_review_flow(tmp_db):
    client = _client()
    pdf = _make_pdf_bytes([
        "Invoice Number: INV-2026-002",
        "Vendor: Bright Office Co",
        "Invoice Date: 2026-10-20",
        "Currency: EUR",
        "Total Amount: 875.00",
    ])
    r = client.post("/api/upload", files={"file": ("invoice_002.pdf", pdf, "application/pdf")})
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["invoice_number"] == "INV-2026-002"
    assert doc["vendor"] == "Bright Office Co"
    assert doc["total_amount"] == 875.00
    assert doc["review_status"] == "pending"

    r = client.post(f"/api/documents/{doc['id']}/review", json={
        "invoice_number": "INV-2026-002",
        "vendor": "Bright Office Co",
        "invoice_date": "2026-10-20",
        "currency": "EUR",
        "total_amount": 875.00,
    })
    assert r.status_code == 200, r.text
    assert r.json()["review_status"] == "confirmed"


def test_upload_rejects_non_pdf(tmp_db):
    client = _client()
    r = client.post("/api/upload", files={"file": ("note.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_upload_rejects_fake_pdf_header(tmp_db):
    client = _client()
    r = client.post("/api/upload", files={"file": ("fake.pdf", b"not a pdf at all", "application/pdf")})
    assert r.status_code == 400


def test_export_only_confirmed(tmp_db):
    client = _client()
    pdf = _make_pdf_bytes([
        "Invoice Number: INV-2026-001",
        "Vendor: Acme Supplies Ltd",
        "Invoice Date: 2026-10-15",
        "Currency: USD",
        "Total Amount: 1240.50",
    ])
    r = client.post("/api/upload", files={"file": ("invoice_001.pdf", pdf, "application/pdf")})
    doc_id = r.json()["id"]

    r = client.get("/api/export?format=csv")
    assert r.status_code == 200
    assert "INV-2026-001" not in r.text  # not confirmed yet -> must not be exported

    client.post(f"/api/documents/{doc_id}/review", json={
        "invoice_number": "INV-2026-001",
        "vendor": "Acme Supplies Ltd",
        "invoice_date": "2026-10-15",
        "currency": "USD",
        "total_amount": 1240.50,
    })
    r = client.get("/api/export?format=csv")
    assert "INV-2026-001" in r.text
    r = client.get("/api/export?format=json")
    assert "INV-2026-001" in r.text


def test_llm_status_is_honest(tmp_db):
    r = _client().get("/api/llm")
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    assert r.json()["default_method"] == "rule"
