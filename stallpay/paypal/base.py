"""PayPal invoicing client interface."""
from __future__ import annotations

from typing import Any, Protocol

from ..models import CheckResult, PaypalInvoice, ProposedOrder


class PaypalClient(Protocol):
    name: str

    def create_invoice(self, order: ProposedOrder, check: CheckResult, invoice_note: str) -> PaypalInvoice:
        ...

    def send_invoice(self, invoice_id: str) -> PaypalInvoice:
        ...

    def get_invoice(self, invoice_id: str) -> PaypalInvoice:
        ...

    def remind(self, invoice_id: str, note: str | None = None) -> PaypalInvoice:
        ...

    def verify_webhook(self, headers: dict[str, str], body: bytes, event: dict[str, Any]) -> bool:
        ...
