"""PayPal webhook handling, with GET-invoice refresh as the backup path."""
from __future__ import annotations

from typing import Any

from . import db
from .paypal.live import PaypalApiError

PAID_EVENTS = {
    "INVOICING.INVOICE.PAID",
    "INVOICING.INVOICE.MARKED_AS_PAID",
}
CANCELLED_EVENTS = {"INVOICING.INVOICE.CANCELLED"}
REFUNDED_EVENTS = {"INVOICING.INVOICE.REFUNDED"}


def map_paypal_status(status: str) -> str:
    value = (status or "").upper()
    if value in {"PAID", "MARKED_AS_PAID"}:
        return "paid"
    if value in {"CANCELLED", "CANCELED"}:
        return "cancelled"
    if value in {"REFUNDED", "PARTIALLY_REFUNDED"}:
        return "refunded"
    if value in {"DRAFT"}:
        return "draft"
    if value in {"SENT", "UNPAID", "PAYMENT_PENDING", "PARTIALLY_PAID", "SCHEDULED", "VIEWED"}:
        return "sent"
    return value.lower() or "unknown"


def invoice_id_from_event(event: dict[str, Any]) -> str | None:
    resource = event.get("resource") or {}
    for candidate in (
        resource.get("id"),
        resource.get("invoice_id"),
        (resource.get("invoice") or {}).get("id"),
    ):
        if candidate:
            return str(candidate)
    return None


def apply_status_update(paypal_invoice_id: str, paypal_status: str, pay_url: str | None = None) -> dict[str, Any] | None:
    record = db.get_invoice_by_paypal_id(paypal_invoice_id)
    if not record:
        return None
    fields: dict[str, Any] = {"status": map_paypal_status(paypal_status)}
    if pay_url:
        fields["pay_url"] = pay_url
    elif record.get("pay_url"):
        pass
    return db.update_invoice(record["id"], **fields)


def handle_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    event_type = str(event.get("event_type") or "")
    paypal_id = invoice_id_from_event(event)
    if not paypal_id:
        return {"ok": False, "reason": "no invoice id in event"}
    if event_type in PAID_EVENTS:
        status = "PAID"
    elif event_type in CANCELLED_EVENTS:
        status = "CANCELLED"
    elif event_type in REFUNDED_EVENTS:
        status = "REFUNDED"
    else:
        resource = event.get("resource") or {}
        status = str(resource.get("status") or "UNKNOWN")
    updated = apply_status_update(paypal_id, status)
    if not updated:
        return {"ok": False, "reason": "invoice not found", "paypal_invoice_id": paypal_id}
    return {"ok": True, "invoice": _public(updated)}


def refresh_from_paypal(record: dict[str, Any], client) -> dict[str, Any]:
    paypal_id = record.get("paypal_invoice_id")
    if not paypal_id:
        raise ValueError("This board row has no PayPal invoice id yet.")
    try:
        invoice = client.get_invoice(paypal_id)
    except PaypalApiError as exc:
        raise ValueError(str(exc)) from exc
    updated = apply_status_update(invoice.invoice_id, invoice.status, invoice.pay_url)
    return updated or record


def _public(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "buyer_name": record["buyer_name"],
        "buyer_email": record["buyer_email"],
        "status": record["status"],
        "paypal_invoice_id": record.get("paypal_invoice_id"),
        "pay_url": record.get("pay_url"),
        "reminder_sent": record.get("reminder_sent"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "check": record.get("check") or {},
        "source": record.get("source"),
    }
