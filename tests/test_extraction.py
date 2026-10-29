from app.extraction import extract_invoice_fields

SAMPLE_TEXT = """MOCK INVOICE - DEMO ONLY

Invoice Number: INV-2026-001
Vendor: Acme Supplies Ltd
Invoice Date: 2026-10-15
Currency: USD
Total Amount: 1240.50
"""


def test_extract_all_fields():
    r = extract_invoice_fields(SAMPLE_TEXT)
    assert r.invoice_number == "INV-2026-001"
    assert r.vendor == "Acme Supplies Ltd"
    assert r.invoice_date == "2026-10-15"
    assert r.currency == "USD"
    assert r.total_amount == 1240.50
    assert r.extraction_method == "rule"


def test_extract_missing_fields_are_none_not_fabricated():
    r = extract_invoice_fields("Invoice Number: INV-2026-009\n")
    assert r.invoice_number == "INV-2026-009"
    assert r.vendor is None
    assert r.invoice_date is None
    assert r.currency is None
    assert r.total_amount is None


def test_extract_empty_text_warns():
    r = extract_invoice_fields("   ")
    assert r.invoice_number is None
    assert any("empty_text" in w for w in r.warnings)
