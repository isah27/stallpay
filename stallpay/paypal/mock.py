"""In-memory PayPal invoicing client so the demo runs without credentials."""
from __future__ import annotations

import secrets
from typing import Any

from ..models import CheckResult, PaypalInvoice, ProposedOrder

_STORE: dict[str, dict[str, Any]] = {}
_NEXT_NUMBER = 1


def reset_store() -> None:
    global _NEXT_NUMBER
    _STORE.clear()
    _NEXT_NUMBER = 1


class MockPaypalClient:
    name = "mock"

    def __init__(self, public_base_url: str) -> None:
        self.public_base_url = public_base_url.rstrip("/")

    def create_invoice(self, order: ProposedOrder, check: CheckResult, invoice_note: str) -> PaypalInvoice:
        global _NEXT_NUMBER
        invoice_id = "MOCK-" + secrets.token_hex(4).upper()
        invoice_number = f"{_NEXT_NUMBER:04d}"
        _NEXT_NUMBER += 1
        record = {
            "id": invoice_id,
            "status": "DRAFT",
            "pay_url": None,
            "buyer_email": order.buyer_email,
            "buyer_name": order.buyer_name,
            "usd_total": str(check.usd_total),
            "invoice_number": invoice_number,
            "note": invoice_note,
            "reminded": False,
        }
        _STORE[invoice_id] = record
        return self._to_invoice(record)

    def send_invoice(self, invoice_id: str) -> PaypalInvoice:
        record = self._require(invoice_id)
        record["status"] = "SENT"
        record["pay_url"] = f"{self.public_base_url}/mock-pay/{invoice_id}"
        return self._to_invoice(record)

    def get_invoice(self, invoice_id: str) -> PaypalInvoice:
        return self._to_invoice(self._require(invoice_id))

    def remind(self, invoice_id: str, note: str | None = None) -> PaypalInvoice:
        record = self._require(invoice_id)
        if record["status"] in {"PAID", "CANCELLED", "REFUNDED"}:
            raise ValueError(f"Cannot remind an invoice in status {record['status']}.")
        record["reminded"] = True
        if note:
            record["remind_note"] = note
        return self._to_invoice(record)

    def mark_paid(self, invoice_id: str) -> PaypalInvoice:
        record = self._require(invoice_id)
        record["status"] = "PAID"
        return self._to_invoice(record)

    def verify_webhook(self, headers: dict[str, str], body: bytes, event: dict[str, Any]) -> bool:
        # Mock events are produced by this app itself.
        return event.get("event_source") == "stallpay-mock" or event.get("event_type", "").startswith("INVOICING.")

    def _require(self, invoice_id: str) -> dict[str, Any]:
        record = _STORE.get(invoice_id)
        if not record:
            raise KeyError(f"Unknown invoice {invoice_id}")
        return record

    def _to_invoice(self, record: dict[str, Any]) -> PaypalInvoice:
        return PaypalInvoice(
            invoice_id=record["id"],
            status=record["status"],
            pay_url=record.get("pay_url"),
            raw=dict(record),
            amount_usd=record.get("usd_total"),
            invoice_number=record.get("invoice_number"),
        )

    def set_status(self, invoice_id: str, status: str) -> PaypalInvoice:
        record = self._require(invoice_id)
        record["status"] = status
        return self._to_invoice(record)
