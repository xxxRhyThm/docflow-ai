"""Deterministic, rule-based extraction for ONE mock invoice format.

This module deliberately does NOT call any LLM. The optional LLM hook in
``llm.py`` is disabled by default and, when enabled, must label its output
as LLM output. Rule results must never be presented as LLM results.

Supported format (one line per field, as generated in samples/):
    Invoice Number: INV-2026-001
    Vendor: Acme Supplies Ltd
    Invoice Date: 2026-10-15
    Currency: USD
    Total Amount: 1240.50
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


@dataclass
class ExtractedInvoice:
    invoice_number: str | None = None
    vendor: str | None = None
    invoice_date: str | None = None
    currency: str | None = None
    total_amount: float | None = None
    extraction_method: str = "rule"
    warnings: list[str] = field(default_factory=list)


# RC2 fix (audit P1): patterns are applied to ONE LINE at a time, and the
# separator after a label is only spaces/tabs ([ \t]*), never \s* which can
# consume a newline. Previously Vendor: on its own line swallowed the next
# line ("Invoice Date: ...") as the vendor value. A blank value on a line
# now stays blank (None) instead of reaching into the next line.
_LINE_PATTERNS = {
    "invoice_number": re.compile(r"^Invoice Number:[ \t]*([A-Za-z0-9\-]+)[ \t]*$"),
    "vendor": re.compile(r"^Vendor:[ \t]*(.+?)[ \t]*$"),
    # RC3: ASCII digits only for the date, matching validation.
    "invoice_date": re.compile(r"^Invoice Date:[ \t]*([0-9]{4}-[0-9]{2}-[0-9]{2})[ \t]*$"),
    "currency": re.compile(r"^Currency:[ \t]*([A-Z]{3})[ \t]*$"),
    # RC3 fix (audit F2): strict thousands grouping only.
    # Allowed: 1240.50 (no grouping) or 1,240.50 (groups of exactly three).
    # NOT allowed: 1,2,3.45, 12,34.56, etc. Those no longer match, so the
    # amount stays None instead of being silently reinterpreted as 123.45.
    "total_amount": re.compile(
        r"^Total Amount:[ \t]*\$?[ \t]*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)\.[0-9]{2})[ \t]*$"
    ),
}


def extract_invoice_fields(text: str) -> ExtractedInvoice:
    """Extract header fields from invoice text. Returns None for missing fields."""
    if not text or not text.strip():
        return ExtractedInvoice(warnings=["empty_text: no text extracted from PDF"])

    result = ExtractedInvoice()
    found: set[str] = set()
    for line in text.splitlines():
        for field_name, pattern in _LINE_PATTERNS.items():
            if field_name in found:
                continue
            match = pattern.search(line)
            if not match:
                continue
            found.add(field_name)
            value = match.group(1).strip()
            if field_name == "total_amount":
                try:
                    amount = float(value.replace(",", ""))
                except ValueError:
                    result.total_amount = None
                    result.warnings.append("unparsable_total_amount")
                else:
                    # RC3 fix (audit §4.2): a 309+ digit amount converts to
                    # inf in Python. Storing inf in SQLite while the API
                    # shows null is inconsistent, so never store it: keep
                    # None and keep the invalid_amount warning.
                    if not math.isfinite(amount):
                        result.total_amount = None
                        result.warnings.append(
                            "invalid_amount: total_amount must be a finite number"
                        )
                    else:
                        result.total_amount = amount
            else:
                setattr(result, field_name, value if value else None)
    return result
