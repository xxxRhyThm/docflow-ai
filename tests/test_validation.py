from app.validation import validate_invoice

VALID = {
    "invoice_number": "INV-2026-001",
    "vendor": "Acme Supplies Ltd",
    "invoice_date": "2026-10-15",
    "currency": "USD",
    "total_amount": 1240.50,
}


def test_valid_invoice_has_no_warnings():
    assert validate_invoice(VALID) == []


def test_missing_fields_reported():
    msgs = validate_invoice({})
    assert any("invoice_number" in m for m in msgs)
    assert any("vendor" in m for m in msgs)
    assert any("invoice_date" in m for m in msgs)
    assert any("currency" in m for m in msgs)
    assert any("total_amount" in m for m in msgs)


def test_invalid_date_reported():
    data = {**VALID, "invoice_date": "2026-02-30"}
    assert any("invalid_date" in m for m in validate_invoice(data))


def test_zero_amount_reported():
    data = {**VALID, "total_amount": 0}
    assert any("invalid_amount" in m for m in validate_invoice(data))


def test_abnormal_amount_flagged_not_silently_accepted():
    data = {**VALID, "total_amount": 2_000_000}
    assert any("abnormal_amount" in m for m in validate_invoice(data))
