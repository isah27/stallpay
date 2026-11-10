"""SQLite persistence for invoice board state."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

_lock = threading.RLock()
_initialized = False


def _connect() -> sqlite3.Connection:
    path: Path = config.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    global _initialized
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    buyer_name TEXT NOT NULL,
                    buyer_email TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    extraction_json TEXT NOT NULL,
                    check_json TEXT NOT NULL,
                    paypal_invoice_id TEXT UNIQUE,
                    status TEXT NOT NULL,
                    pay_url TEXT,
                    reminder_sent INTEGER NOT NULL DEFAULT 0,
                    source TEXT,
                    notes TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def insert_invoice(row: dict[str, Any]) -> dict[str, Any]:
    init_db()
    now = _now()
    with _lock:
        conn = _connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO invoices (
                    created_at, updated_at, buyer_name, buyer_email, raw_text,
                    extraction_json, check_json, paypal_invoice_id, status,
                    pay_url, reminder_sent, source, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    now,
                    row["buyer_name"],
                    row["buyer_email"],
                    row.get("raw_text") or "",
                    json.dumps(row.get("extraction") or {}),
                    json.dumps(row.get("check") or {}),
                    row.get("paypal_invoice_id"),
                    row["status"],
                    row.get("pay_url"),
                    1 if row.get("reminder_sent") else 0,
                    row.get("source") or "",
                    row.get("notes") or "",
                ),
            )
            conn.commit()
            pk = cursor.lastrowid
        finally:
            conn.close()
    return get_invoice_by_pk(pk)  # type: ignore[arg-type]


def list_invoices() -> list[dict[str, Any]]:
    init_db()
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_invoice_by_pk(pk: int) -> dict[str, Any] | None:
    init_db()
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (pk,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_invoice_by_paypal_id(paypal_id: str) -> dict[str, Any] | None:
    init_db()
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM invoices WHERE paypal_invoice_id = ?", (paypal_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def update_invoice(pk: int, **fields: Any) -> dict[str, Any] | None:
    init_db()
    if not fields:
        return get_invoice_by_pk(pk)
    allowed = {
        "status",
        "pay_url",
        "reminder_sent",
        "paypal_invoice_id",
        "notes",
        "check_json",
        "extraction_json",
    }
    assignments = []
    values: list[Any] = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key == "reminder_sent":
            value = 1 if value else 0
        assignments.append(f"{key} = ?")
        values.append(value)
    if not assignments:
        return get_invoice_by_pk(pk)
    assignments.append("updated_at = ?")
    values.append(_now())
    values.append(pk)
    with _lock:
        conn = _connect()
        try:
            conn.execute(f"UPDATE invoices SET {', '.join(assignments)} WHERE id = ?", values)
            conn.commit()
        finally:
            conn.close()
    return get_invoice_by_pk(pk)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["reminder_sent"] = bool(data.get("reminder_sent"))
    try:
        data["extraction"] = json.loads(data.get("extraction_json") or "{}")
    except json.JSONDecodeError:
        data["extraction"] = {}
    try:
        data["check"] = json.loads(data.get("check_json") or "{}")
    except json.JSONDecodeError:
        data["check"] = {}
    return data
