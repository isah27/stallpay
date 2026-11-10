"""Seller-tone reminders and a written morning briefing, with optional speech in the browser."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from . import config
from .llm_client import LlmError, complete
from .money import format_money, format_usd, parse_amount
from .shops import get_shop


def draft_remind_note(record: dict[str, Any], tone: str | None = None, language: str | None = None) -> str:
    buyer = record.get("buyer_name") or "there"
    check = record.get("check") or {}
    currency = check.get("currency") or "NGN"
    total = parse_amount(check.get("computed_total") or check.get("computed_total_ngn")) or Decimal("0")
    display = format_money(total, currency)
    invoice_id = record.get("paypal_invoice_id") or "your invoice"
    language = language or _language_from_record(record)
    fallback = {
        "pcm": f"Good day {buyer}. Your StallPay invoice {invoice_id} for {display} still dey unpaid. Abeg use the pay link when you ready.",
        "es": f"Hola {buyer}. Tu factura de StallPay {invoice_id} por {display} sigue pendiente. Cuando puedas, usa el enlace de pago.",
        "hi": f"Namaste {buyer}. StallPay invoice {invoice_id} ({display}) abhi pending hai. Jab ho sake, pay link se payment kar dena.",
    }.get(language, f"Hello {buyer}. This is a gentle reminder that StallPay invoice {invoice_id} for {display} is still unpaid. Please use the pay link when you can.")
    if not config.LLM_AVAILABLE:
        return fallback
    try:
        text = complete(
            "Write one short unpaid-invoice reminder in the seller's tone. "
            "No threats, no new discount, no claim that payment already arrived. "
            "Return only the reminder text. Sandbox / demo wording is fine.",
            f"Tone: {tone or 'polite and warm'}. Language: {language}. Buyer: {buyer}. "
            f"Invoice: {invoice_id}. Amount: {display}.",
            max_tokens=180,
            temperature=0.4,
            timeout=15.0,
        )
        cleaned = (text or "").strip().strip('"')
        return cleaned[:400] if cleaned else fallback
    except (LlmError, Exception):
        return fallback


def morning_briefing(invoices: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in invoices if row.get("status") in {"sent", "paid", "refunded"} or row.get("paypal_invoice_id")]
    paid = [row for row in invoices if row.get("status") == "paid"]
    unpaid = [row for row in invoices if row.get("status") in {"sent", "draft"}]
    paid_usd = Decimal("0.00")
    unpaid_names = []
    by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for row in paid:
        check = row.get("check") or {}
        usd = parse_amount(check.get("usd_total")) or Decimal("0")
        paid_usd += usd
        currency = check.get("currency") or "NGN"
        local = parse_amount(check.get("computed_total") or check.get("computed_total_ngn")) or Decimal("0")
        by_currency[currency] += local
    for row in unpaid:
        check = row.get("check") or {}
        currency = check.get("currency") or "NGN"
        local = parse_amount(check.get("computed_total") or check.get("computed_total_ngn"))
        label = row.get("buyer_name") or "a buyer"
        if local is not None:
            unpaid_names.append(f"{label} still owes {format_money(local, currency)}")
        else:
            unpaid_names.append(f"{label} still owes an unpaid invoice")

    local_bits = ", ".join(f"{format_money(total, code)} closed in {code}" for code, total in by_currency.items()) or "no paid totals yet"
    unpaid_bit = "; ".join(unpaid_names) if unpaid_names else "nobody still owes"
    text = (
        f"Good morning. {len(paid)} sale{'s' if len(paid) != 1 else ''} landed, "
        f"{format_usd(paid_usd)} in PayPal, {local_bits}. "
        f"{len(unpaid)} still unpaid: {unpaid_bit}. "
        f"{len(closed)} invoice{'s' if len(closed) != 1 else ''} are on the board in total."
    )
    if config.LLM_AVAILABLE and invoices:
        try:
            drafted = complete(
                "Rewrite this seller morning briefing in a warm, concise spoken style, 3 sentences max. "
                "Keep the numbers and names accurate. Return only the spoken text.",
                text,
                max_tokens=220,
                temperature=0.3,
                timeout=15.0,
            )
            cleaned = (drafted or "").strip().strip('"')
            if cleaned:
                text = cleaned[:800]
        except (LlmError, Exception):
            pass
    return {
        "text": text,
        "paid_count": len(paid),
        "unpaid_count": len(unpaid),
        "paid_usd": str(paid_usd),
        "paid_usd_display": format_usd(paid_usd),
        "language": "en",
        "speech": {
            "text": text,
            "lang": "en-US",
            "engine": "browser-speech-synthesis",
            "fallback": text,
        },
    }


def _language_from_record(record: dict[str, Any]) -> str:
    source = (record.get("source") or "") + " " + str(record.get("shop_id") or "")
    extraction = record.get("extraction") or {}
    currency = (extraction.get("currency") or (record.get("check") or {}).get("currency") or "").upper()
    if currency == "MXN":
        return "es"
    if currency == "INR":
        return "hi"
    if currency == "NGN":
        return "pcm"
    return "en"
