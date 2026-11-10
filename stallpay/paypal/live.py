"""Live PayPal sandbox Invoicing API client. Credentials stay in environment variables."""
from __future__ import annotations

import time
from typing import Any

import httpx

from .. import config
from ..models import CheckResult, PaypalInvoice, ProposedOrder


class PaypalApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LivePaypalClient:
    name = "live"

    def __init__(self) -> None:
        self.base = config.PAYPAL_API_BASE.rstrip("/")
        self._token: str | None = None
        self._token_expiry = 0.0

    def create_invoice(self, order: ProposedOrder, check: CheckResult, invoice_note: str) -> PaypalInvoice:
        items = []
        for row in check.usd_items:
            items.append(
                {
                    "name": row.name[:200],
                    "quantity": str(row.quantity),
                    "unit_amount": {"currency_code": "USD", "value": f"{row.unit_price_usd:.2f}"},
                }
            )
        given, surname = _split_name(order.buyer_name)
        payload = {
            "detail": {
                "currency_code": "USD",
                "note": invoice_note[:4000],
                "payment_term": {"term_type": "DUE_ON_RECEIPT"},
            },
            "invoicer": {
                "name": {
                    "given_name": config.PAYPAL_INVOICER_GIVEN_NAME,
                    "surname": config.PAYPAL_INVOICER_SURNAME,
                },
                "email_address": config.PAYPAL_INVOICER_EMAIL,
                "business_name": config.PAYPAL_INVOICER_BUSINESS_NAME,
            },
            "primary_recipients": [
                {
                    "billing_info": {
                        "name": {"given_name": given, "surname": surname},
                        "email_address": order.buyer_email,
                    }
                }
            ],
            "items": items,
        }
        data, _ = self._request("POST", "/v2/invoicing/invoices", json=payload, expected=(200, 201))
        return self._invoice_from_api(data)

    def send_invoice(self, invoice_id: str) -> PaypalInvoice:
        # Share the pay link from the app. Do not email the recipient automatically,
        # so a pasted real-world address is not contacted.
        self._request(
            "POST",
            f"/v2/invoicing/invoices/{invoice_id}/send",
            json={"send_to_recipient": False, "send_to_invoicer": False},
            expected=(200, 202),
        )
        return self.get_invoice(invoice_id)

    def get_invoice(self, invoice_id: str) -> PaypalInvoice:
        data, _ = self._request("GET", f"/v2/invoicing/invoices/{invoice_id}", expected=(200,))
        return self._invoice_from_api(data)

    def remind(self, invoice_id: str, note: str | None = None) -> PaypalInvoice:
        body: dict[str, Any] = {"send_to_recipient": True, "send_to_invoicer": False}
        if note:
            body["note"] = note[:4000]
        self._request(
            "POST",
            f"/v2/invoicing/invoices/{invoice_id}/remind",
            json=body,
            expected=(200, 204),
        )
        invoice = self.get_invoice(invoice_id)
        invoice.raw["reminded"] = True
        return invoice

    def verify_webhook(self, headers: dict[str, str], body: bytes, event: dict[str, Any]) -> bool:
        webhook_id = config.PAYPAL_WEBHOOK_ID.strip()
        if not webhook_id:
            return False
        transmission_id = _header(headers, "PayPal-Transmission-Id")
        timestamp = _header(headers, "PayPal-Transmission-Time")
        signature = _header(headers, "PayPal-Transmission-Sig")
        cert_url = _header(headers, "PayPal-Cert-Url")
        auth_algo = _header(headers, "PayPal-Auth-Algo")
        if not all([transmission_id, timestamp, signature, cert_url, auth_algo]):
            return False
        payload = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": signature,
            "transmission_time": timestamp,
            "webhook_id": webhook_id,
            "webhook_event": event,
        }
        try:
            data, _ = self._request(
                "POST",
                "/v1/notifications/verify-webhook-signature",
                json=payload,
                expected=(200,),
            )
        except PaypalApiError:
            return False
        return str(data.get("verification_status", "")).upper() == "SUCCESS"

    def _invoice_from_api(self, data: dict[str, Any]) -> PaypalInvoice:
        invoice_id = data.get("id") or _href_id(data)
        status = (
            (data.get("status") or data.get("detail", {}).get("status") or "UNKNOWN")
        )
        pay_url = _pay_url(data)
        if not invoice_id:
            raise PaypalApiError("PayPal create/get response did not include an invoice id.")
        amount_usd = _amount_usd(data)
        return PaypalInvoice(
            invoice_id=str(invoice_id),
            status=str(status),
            pay_url=pay_url,
            raw=data,
            amount_usd=amount_usd,
        )

    def record_payment(self, invoice_id: str, amount_usd: str | None = None) -> PaypalInvoice:
        """Record a sandbox payment against an invoice (invoicer-side). Never used by receipt uploads."""
        from datetime import date

        invoice = self.get_invoice(invoice_id)
        value = amount_usd or invoice.amount_usd
        if not value:
            raise PaypalApiError("Cannot record a payment without an amount.")
        payload = {
            "method": "OTHER",
            "payment_date": date.today().isoformat(),
            "amount": {"currency_code": "USD", "value": f"{value}"},
        }
        self._request(
            "POST",
            f"/v2/invoicing/invoices/{invoice_id}/payments",
            json=payload,
            expected=(200, 201, 204),
        )
        return self.get_invoice(invoice_id)

    def _request(
        self,
        method: str,
        path: str,
        expected: tuple[int, ...],
        json: dict[str, Any] | None = None,
    ) -> tuple[Any, httpx.Response]:
        token = self._access_token()
        # Do not log headers: they carry the bearer token.
        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                method,
                f"{self.base}{path}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json,
            )
        if response.status_code not in expected:
            detail = _safe_error(response)
            raise PaypalApiError(f"PayPal {method} {path} failed ({response.status_code}): {detail}", response.status_code)
        if response.status_code == 204 or not response.content:
            return {}, response
        try:
            return response.json(), response
        except Exception:
            return {}, response

    def _access_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expiry - 30:
            return self._token
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(config.PAYPAL_CLIENT_ID, config.PAYPAL_CLIENT_SECRET),
            )
        if response.status_code != 200:
            raise PaypalApiError(
                f"PayPal authentication failed ({response.status_code}). Check the sandbox client id and secret.",
                response.status_code,
            )
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise PaypalApiError("PayPal authentication returned no access token.")
        expires = int(data.get("expires_in") or 300)
        self._token = token
        self._token_expiry = now + expires
        return token



def _amount_usd(data: dict[str, Any]) -> str | None:
    candidates = []
    due = data.get("due_amount") or {}
    if isinstance(due, dict) and due.get("value") and str(due.get("currency_code") or "USD").upper() == "USD":
        # A paid invoice often has due_amount 0; prefer total if present.
        candidates.append(due.get("value"))
    amount = data.get("amount") or {}
    if isinstance(amount, dict):
        if amount.get("value"):
            candidates.append(amount.get("value"))
        breakdown = amount.get("breakdown") or {}
        if isinstance(breakdown, dict):
            item_total = breakdown.get("item_total") or breakdown.get("total") or {}
            if isinstance(item_total, dict) and item_total.get("value"):
                candidates.append(item_total.get("value"))
    detail = data.get("detail") or {}
    if isinstance(detail, dict) and isinstance(detail.get("amount"), dict):
        candidates.append(detail["amount"].get("value"))
    for value in candidates:
        if value and str(value) not in {"0", "0.00"}:
            return str(value)
    return str(candidates[0]) if candidates else None

def _split_name(full: str) -> tuple[str, str]:
    parts = [p for p in full.strip().split() if p]
    if not parts:
        return "Buyer", "Customer"
    if len(parts) == 1:
        return parts[0], "Customer"
    return parts[0], " ".join(parts[1:])


def _header(headers: dict[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def _href_id(data: dict[str, Any]) -> str | None:
    href = data.get("href") or ""
    if "/invoices/" in href:
        return href.rstrip("/").split("/invoices/")[-1].split("/")[0]
    for link in data.get("links") or []:
        href = link.get("href") or ""
        if "/invoices/" in href and link.get("rel") in {"self", "edit", None, "get"}:
            return href.rstrip("/").split("/invoices/")[-1].split("/")[0]
    return None


def _pay_url(data: dict[str, Any]) -> str | None:
    meta = (data.get("detail") or {}).get("metadata") or {}
    for key in ("recipient_view_url", "buyer_view_url", "payer_view_url"):
        if meta.get(key):
            return str(meta[key])
    for link in data.get("links") or []:
        rel = (link.get("rel") or "").lower()
        if rel in {"payer-view", "recipient-view", "approve"}:
            return str(link.get("href"))
    if data.get("href") and "invoice/p" in str(data.get("href")):
        return str(data["href"])
    return None


def _safe_error(response: httpx.Response) -> str:
    try:
        data = response.json()
    except Exception:
        return "request was rejected"
    if isinstance(data, dict):
        if data.get("message"):
            return str(data["message"])
        details = data.get("details")
        if isinstance(details, list) and details:
            first = details[0]
            if isinstance(first, dict):
                return str(first.get("description") or first.get("issue") or "request was rejected")
        if data.get("name"):
            return str(data["name"])
    return "request was rejected"
