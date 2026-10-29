"""Independent RC2 audit tests. Point PYTHONPATH at the extracted project.

Run: python -m pytest -v test_rc2_audit_boundaries.py
These assertions express audit expectations; failures must remain visible.
"""
import csv
import io
import json
import math

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.extraction import extract_invoice_fields

FIELDS = dict(invoice_number="INV-2026-901", vendor="Independent Audit",
              invoice_date="2026-10-29", currency="USD", total_amount=42.50)


def pdf_bytes(total="42.50", pages=1, vendor="Independent Audit"):
    pdf = pymupdf.open()
    for n in range(pages):
        page = pdf.new_page()
        lines = ["Invoice Number: INV-2026-901", f"Vendor: {vendor}",
                 "Invoice Date: 2026-10-29", "Currency: USD", f"Total Amount: {total}"]
        # Tiny text keeps deliberately huge numeric inputs on a single normal page.
        for i, line in enumerate(lines):
            page.insert_text((20, 30 + i * 20), line, fontsize=1 if i == 4 else 10)
    data = pdf.tobytes()
    pdf.close()
    return data


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFLOW_DB_PATH", str(tmp_path / "independent.db"))
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def upload(client, **kwargs):
    return client.post("/api/upload", files={"file": ("audit.pdf", pdf_bytes(**kwargs), "application/pdf")})


def new_document(client):
    response = upload(client)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("amount", ["NaN", "Infinity", "-Infinity", '"NaN"', '"Infinity"', "1e309", '"1e309"'])
@pytest.mark.parametrize("confirmed", [False, True])
def test_nonfinite_rejected_and_existing_state_preserved(client, amount, confirmed):
    doc = new_document(client)
    url = f"/api/documents/{doc['id']}/review"
    if confirmed:
        assert client.post(url, json=FIELDS).status_code == 200
    before = client.get(f"/api/documents/{doc['id']}").json()
    raw = json.dumps({**FIELDS, "total_amount": "PLACEHOLDER"}).replace('"PLACEHOLDER"', amount)
    result = client.post(url, content=raw, headers={"Content-Type": "application/json"})
    assert result.status_code == 400, result.text
    assert client.get(f"/api/documents/{doc['id']}").json() == before
    exported = client.get("/api/export?format=json").json()
    assert len(exported) == int(confirmed)
    if confirmed:
        assert exported[0]["total_amount"] == FIELDS["total_amount"]


@pytest.mark.parametrize("field", ["invoice_number", "vendor", "invoice_date", "currency"])
@pytest.mark.parametrize("value", [" \t\r\n ", "\u00a0\u3000", None])
def test_blank_fields_rejected_without_write(client, field, value):
    doc = new_document(client)
    before = client.get(f"/api/documents/{doc['id']}").json()
    result = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, field: value})
    assert result.status_code == 400, result.text
    assert client.get(f"/api/documents/{doc['id']}").json() == before


@pytest.mark.parametrize("date", ["2026-1-02", "2026-01-2", "2026-02-29", "2026-02-30", "0000-01-01", "2026-10-29T00:00:00", "2026-10-29x", "２０２６-10-29"])
def test_invalid_dates_rejected(client, date):
    doc = new_document(client)
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, "invoice_date": date})
    assert r.status_code == 400, r.text


@pytest.mark.parametrize("date", ["2024-02-29", "2000-02-29", "2026-01-02"])
def test_valid_calendar_dates(client, date):
    doc = new_document(client)
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, "invoice_date": date})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("field,length", [("vendor", 201), ("invoice_number", 51)])
def test_length_limits_block_confirmation(client, field, length):
    doc = new_document(client)
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, field: "A" * length})
    assert r.status_code == 400, r.text


@pytest.mark.parametrize("label,field", [("Invoice Number", "invoice_number"), ("Vendor", "vendor"), ("Invoice Date", "invoice_date"), ("Currency", "currency"), ("Total Amount", "total_amount")])
def test_blank_label_never_consumes_next_line(label, field):
    result = extract_invoice_fields(f"{label}: \t\nVendor: Following Line\nInvoice Date: 2026-10-29")
    # Skip creating a second occurrence of the field being tested.
    if field in ("vendor", "invoice_date"):
        result = extract_invoice_fields(f"{label}: \t\nCurrency: USD\nTotal Amount: 42.50")
    assert getattr(result, field) is None


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r", "\n", " \t="])
def test_csv_cells_are_text_and_roundtrip(client, prefix):
    doc = new_document(client)
    vendor = prefix + '2+2,"quoted"'
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, "vendor": vendor})
    assert r.status_code == 200, r.text
    rows = list(csv.DictReader(io.StringIO(client.get("/api/export?format=csv").text)))
    assert len(rows) == 1
    cleaned = vendor.strip()
    expected = "'" + cleaned if cleaned[0] in "=+-@\t\r" else cleaned
    assert rows[0]["vendor"] == expected


def test_duplicate_warning_and_documented_double_export(client):
    first, second = new_document(client), new_document(client)
    assert any("duplicate_invoice_number" in w for w in second["warnings"])
    for doc in (first, second):
        r = client.post(f"/api/documents/{doc['id']}/review", json=FIELDS)
        assert r.status_code == 200
        assert any("duplicate_invoice_number" in w for w in r.json()["warnings"])
    assert len(client.get("/api/export?format=json").json()) == 2


@pytest.mark.parametrize("pages,status", [(20, 200), (21, 400)])
def test_pdf_page_limit(client, pages, status):
    assert upload(client, pages=pages).status_code == status


def test_exact_upload_size_boundary(client):
    data = pdf_bytes()
    limit = 10 * 1024 * 1024
    at_limit = data + b" " * (limit - len(data))
    assert client.post("/api/upload", files={"file": ("limit.pdf", at_limit, "application/pdf")}).status_code == 200
    assert client.post("/api/upload", files={"file": ("limit.pdf", at_limit + b" ", "application/pdf")}).status_code == 413


def test_sql_metacharacters_stored_as_data(client):
    doc = new_document(client)
    vendor = "'; DROP TABLE documents; --"
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, "vendor": vendor})
    assert r.status_code == 200 and r.json()["vendor"] == vendor
    assert len(client.get("/api/documents").json()) == 1


def test_huge_pdf_amount_does_not_poison_database(client):
    r = upload(client, total="9" * 310 + ".00")
    assert r.status_code in (200, 400), f"upload returned {r.status_code}: {r.text}"
    listed = client.get("/api/documents")
    assert listed.status_code == 200, listed.text
    for doc in listed.json():
        assert doc["total_amount"] is None or math.isfinite(doc["total_amount"])


def test_boolean_amount_is_not_money(client):
    doc = new_document(client)
    r = client.post(f"/api/documents/{doc['id']}/review", json={**FIELDS, "total_amount": True})
    assert r.status_code in (400, 422), r.text
    assert client.get(f"/api/documents/{doc['id']}").json()["review_status"] == "pending"


def test_malformed_grouping_not_silently_changed():
    result = extract_invoice_fields("Total Amount: 1,2,3.45")
    assert result.total_amount is None, f"invalid grouping became {result.total_amount}"


def test_invalid_nan_string_field_returns_client_error(client):
    doc = new_document(client)
    raw = json.dumps({**FIELDS, "vendor": "PLACEHOLDER"}).replace('"PLACEHOLDER"', "NaN")
    r = client.post(f"/api/documents/{doc['id']}/review", content=raw, headers={"Content-Type": "application/json"})
    assert r.status_code in (400, 422), r.text

