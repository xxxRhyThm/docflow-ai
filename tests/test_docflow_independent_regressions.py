"""Independent release-gate regressions for DocFlow AI RC.

Run with:
  PYTHONPATH=<path-to-docflow-ai-rc> python -m pytest -q test_docflow_independent_regressions.py

Expected behavior: reject invalid values rather than confirm/export them.
Tests intentionally fail on the uploaded RC to demonstrate the remaining bugs.
"""
import io
import json

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app


def _pdf(lines):
    document = pymupdf.open()
    page = document.new_page()
    for pos, line in enumerate(lines):
        page.insert_text((72, 72 + 22 * pos), line)
    result = document.tobytes()
    document.close()
    return result


@pytest.fixture()
def session(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCFLOW_DB_PATH", str(tmp_path / "audit.db"))
    client = TestClient(app, raise_server_exceptions=False)
    lines = [
        "Invoice Number: INV-2026-001",
        "Vendor: Acme Supplies Ltd",
        "Invoice Date: 2026-10-15",
        "Currency: USD",
        "Total Amount: 10.00",
    ]
    result = client.post("/api/upload", files={"file": ("sample.pdf", _pdf(lines), "application/pdf")})
    assert result.status_code == 200
    return client, result.json()


def _fields(record):
    return {key: record.get(key) for key in
            ("invoice_number", "vendor", "invoice_date", "currency", "total_amount")}


@pytest.mark.parametrize("amount", ("NaN", "Infinity"))
def test_special_float_must_not_confirm_or_export(session, amount):
    client, document = session
    payload = {**_fields(document), "total_amount": 10.0}
    encoded = json.dumps(payload).replace('"total_amount": 10.0', f'"total_amount": {amount}')
    response = client.post(f'/api/documents/{document["id"]}/review',
                           content=encoded, headers={"content-type": "application/json"})
    assert response.status_code == 400, response.text
    after = client.get(f'/api/documents/{document["id"]}').json()
    assert after['review_status'] == 'pending'


def test_whitespace_vendor_must_block_confirmation(session):
    client, document = session
    payload = {**_fields(document), "vendor": " \t "}
    response = client.post(f'/api/documents/{document["id"]}/review', json=payload)
    assert response.status_code == 400, response.text


def test_blank_vendor_not_filled_from_next_line(tmp_path, monkeypatch):
    monkeypatch.setenv('DOCFLOW_DB_PATH', str(tmp_path / 'audit2.db'))
    client = TestClient(app)
    lines = [
        "Invoice Number: INV-2026-002",
        "Vendor:",
        "Invoice Date: 2026-10-15",
        "Currency: USD",
        "Total Amount: 10.00",
    ]
    result = client.post('/api/upload', files={'file': ('blank.pdf', _pdf(lines), 'application/pdf')})
    assert result.status_code == 200
    actual = result.json()
    assert actual['vendor'] is None, actual
    assert any('vendor' in message for message in actual['warnings'])


def test_noncanonical_date_rejected(session):
    client, document = session
    payload = {**_fields(document), 'invoice_date': '2026-1-2'}
    response = client.post(f'/api/documents/{document["id"]}/review', json=payload)
    assert response.status_code == 400, response.text
