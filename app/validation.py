"""Validation for extracted invoice fields.

Rules are intentionally narrow for v1 (single invoice format):
- missing field -> error
- date must be a real calendar date in YYYY-MM-DD
- total amount must be > 0; > 1,000,000 is flagged as abnormal, not rejected
- currency must be one of the supported codes; anything else is a warning
- invoice number should match INV-YYYY-NNN, otherwise a warning
"""

from __future__ import annotations

import math
import re
from datetime import datetime

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "CNY"}
# RC3 fix (audit F3): use [0-9], not \d. Python \d matches Unicode digits,
# so a full-width year like ２０２６ passed the old regex and strptime.
_INVOICE_RE = re.compile(r"^INV-[0-9]{4}-[0-9]{3}$")
# RC2 fix (audit P2): date must be exactly YYYY-MM-DD, zero-padded.
# strptime alone accepts 2026-1-2, so the regex runs first.
# RC3: ASCII digits only, enforced with fullmatch semantics via ^...$.
_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
# RC2: conservative length caps for free-text fields (audit: reasonable length).
_MAX_LEN = {"invoice_number": 50, "vendor": 200, "invoice_date": 10, "currency": 3}


def _clean(value):
    """Strip a string field; blank-after-strip becomes None (RC2, audit P1)."""
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def blocking_errors(messages: list[str]) -> list[str]:
    """Messages that must block confirmation (RC fix, issue 3/4).

    Missing fields, invalid dates/amounts and unsupported currencies are
    errors. Format warnings and abnormal-amount flags are warnings: they are
    shown to the reviewer but do not by themselves block confirmation.
    """
    prefixes = ("missing_field:", "invalid_", "unsupported_")
    return [m for m in messages if m.startswith(prefixes)]


def validate_invoice(data: dict) -> list[str]:
    """Return a list of human-readable validation messages (empty = valid).

    RC2 changes: every string field is stripped first, so a value that is
    only spaces/tabs counts as missing; the date must match YYYY-MM-DD
    exactly AND be a real calendar date; a non-finite amount (NaN/Infinity)
    is an invalid amount, not a silent pass.
    """
    messages: list[str] = []

    invoice_number = _clean(data.get("invoice_number"))
    if not invoice_number:
        messages.append("missing_field: invoice_number")
    elif len(invoice_number) > _MAX_LEN["invoice_number"]:
        messages.append("invalid_invoice_number: invoice_number is too long")
    elif not _INVOICE_RE.match(invoice_number):
        messages.append("format_warning: invoice_number should look like INV-2026-001")

    vendor = _clean(data.get("vendor"))
    if not vendor:
        messages.append("missing_field: vendor")
    elif len(vendor) > _MAX_LEN["vendor"]:
        messages.append("invalid_vendor: vendor is too long")

    date_text = _clean(data.get("invoice_date"))
    if not date_text:
        messages.append("missing_field: invoice_date")
    elif not _DATE_RE.match(date_text):
        messages.append(f"invalid_date: {date_text} is not in YYYY-MM-DD format")
    else:
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            messages.append(f"invalid_date: {date_text} is not a real calendar date (YYYY-MM-DD)")

    currency = _clean(data.get("currency"))
    if not currency:
        messages.append("missing_field: currency")
    elif currency not in SUPPORTED_CURRENCIES:
        messages.append(f"unsupported_currency: {currency}")

    total = data.get("total_amount")
    if total is None or (isinstance(total, str) and not total.strip()):
        messages.append("missing_field: total_amount")
    elif isinstance(total, bool):
        # RC3 fix (audit F1): bool is a subclass of int in Python, so
        # float(True) == 1.0 would otherwise silently become money.
        messages.append("invalid_amount: total_amount must be a number, not a boolean")
    else:
        try:
            amount = float(total)
        except (TypeError, ValueError):
            messages.append(f"invalid_amount: {total!r} is not a number")
        else:
            # RC2 fix (audit P0): NaN compares False to every number, so the
            # old <=0 / >1,000,000 checks let it through, and SQLite then
            # stored it as NULL while the document became confirmed.
            if not math.isfinite(amount):
                messages.append("invalid_amount: total_amount must be a finite number")
            elif amount <= 0:
                messages.append("invalid_amount: total_amount must be greater than 0")
            elif amount > 1_000_000:
                messages.append("abnormal_amount: total_amount exceeds 1,000,000, please double-check")

    return messages
