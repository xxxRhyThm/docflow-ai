# Expected extraction results (mock data, demo only)

All three files use the single v1 invoice format. Amounts are fictitious.

| File | Invoice number | Vendor | Date | Currency | Total | Expected warnings |
|---|---|---|---|---|---|---|
| invoice_001.pdf | INV-2026-001 | Acme Supplies Ltd | 2026-10-15 | USD | 1240.50 | none |
| invoice_002.pdf | INV-2026-002 | Bright Office Co | 2026-10-20 | EUR | 875.00 | none |
| invoice_003.pdf | INV-2026-003 | Northwind Trading | 2026-10-28 | USD | 0.00 | invalid_amount: total_amount must be greater than 0 |

Invoice 003 is intentionally abnormal: a zero total must be flagged in review
and corrected by a human before confirmation. It must never be silently
exported as a valid invoice.
