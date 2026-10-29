"""SQLite storage. No credentials, no external service.

The database path can be overridden with the DOCFLOW_DB_PATH environment
variable, which is how the test suite uses a temporary database.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "docflow.db"


def db_path() -> Path:
    override = os.environ.get("DOCFLOW_DB_PATH")
    return Path(override) if override else DEFAULT_DB


def get_connection() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            status TEXT NOT NULL,
            invoice_number TEXT,
            vendor TEXT,
            invoice_date TEXT,
            currency TEXT,
            total_amount REAL,
            warnings_json TEXT NOT NULL DEFAULT '[]',
            review_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["warnings"] = json.loads(data.pop("warnings_json") or "[]")
    return data


def insert_document(filename: str, extracted: dict, warnings: list[str]) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO documents
                (original_filename, status, invoice_number, vendor,
                 invoice_date, currency, total_amount, warnings_json, review_status)
            VALUES (?, 'extracted', ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                filename,
                extracted.get("invoice_number"),
                extracted.get("vendor"),
                extracted.get("invoice_date"),
                extracted.get("currency"),
                extracted.get("total_amount"),
                json.dumps(warnings, ensure_ascii=False),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def list_documents() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def find_duplicate_invoice_numbers(invoice_number: str | None, exclude_id: int | None = None) -> list[int]:
    """Return ids of other documents with the same invoice number (RC, issue 8)."""
    if not invoice_number:
        return []
    conn = get_connection()
    try:
        if exclude_id is None:
            rows = conn.execute(
                "SELECT id FROM documents WHERE invoice_number = ?", (invoice_number,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id FROM documents WHERE invoice_number = ? AND id != ?",
                (invoice_number, exclude_id),
            ).fetchall()
        return [r["id"] for r in rows]
    finally:
        conn.close()


def get_document(doc_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def update_review(doc_id: int, fields: dict, warnings: list[str]) -> dict | None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE documents
            SET invoice_number = ?, vendor = ?, invoice_date = ?,
                currency = ?, total_amount = ?, warnings_json = ?,
                status = 'confirmed', review_status = 'confirmed'
            WHERE id = ?
            """,
            (
                fields.get("invoice_number"),
                fields.get("vendor"),
                fields.get("invoice_date"),
                fields.get("currency"),
                fields.get("total_amount"),
                json.dumps(warnings, ensure_ascii=False),
                doc_id,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()
