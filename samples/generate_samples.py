"""Generate three fictitious mock invoices (English, single format).

All names, numbers and amounts are invented for demo purposes only.
Run from the project root:
    python samples/generate_samples.py
Output: samples/invoice_001.pdf, invoice_002.pdf, invoice_003.pdf
"""

from pathlib import Path

import pymupdf as fitz  # PyMuPDF (avoids deprecated fitz import warning)

SAMPLES = [
    {
        "filename": "invoice_001.pdf",
        "lines": [
            "MOCK INVOICE - DEMO ONLY",
            "",
            "Invoice Number: INV-2026-001",
            "Vendor: Acme Supplies Ltd",
            "Invoice Date: 2026-10-15",
            "Currency: USD",
            "Total Amount: 1240.50",
            "",
            "Items: Office supplies - 10 units",
        ],
        "expected": {
            "invoice_number": "INV-2026-001",
            "vendor": "Acme Supplies Ltd",
            "invoice_date": "2026-10-15",
            "currency": "USD",
            "total_amount": 1240.50,
            "expected_warnings": [],
        },
    },
    {
        "filename": "invoice_002.pdf",
        "lines": [
            "MOCK INVOICE - DEMO ONLY",
            "",
            "Invoice Number: INV-2026-002",
            "Vendor: Bright Office Co",
            "Invoice Date: 2026-10-20",
            "Currency: EUR",
            "Total Amount: 875.00",
            "",
            "Items: Printer paper - 20 packs",
        ],
        "expected": {
            "invoice_number": "INV-2026-002",
            "vendor": "Bright Office Co",
            "invoice_date": "2026-10-20",
            "currency": "EUR",
            "total_amount": 875.00,
            "expected_warnings": [],
        },
    },
    {
        "filename": "invoice_003.pdf",
        "lines": [
            "MOCK INVOICE - DEMO ONLY",
            "",
            "Invoice Number: INV-2026-003",
            "Vendor: Northwind Trading",
            "Invoice Date: 2026-10-28",
            "Currency: USD",
            "Total Amount: 0.00",
            "",
            "Items: Sample goods - 1 unit (total intentionally zero to demo validation)",
        ],
        "expected": {
            "invoice_number": "INV-2026-003",
            "vendor": "Northwind Trading",
            "invoice_date": "2026-10-28",
            "currency": "USD",
            "total_amount": 0.00,
            "expected_warnings": ["invalid_amount: total_amount must be greater than 0"],
        },
    },
]


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    for sample in SAMPLES:
        doc = fitz.open()
        page = doc.new_page()
        y = 72
        for line in sample["lines"]:
            page.insert_text((72, y), line, fontsize=12)
            y += 22
        doc.save(out_dir / sample["filename"])
        doc.close()
        print(f"Wrote {sample['filename']}")


if __name__ == "__main__":
    main()
