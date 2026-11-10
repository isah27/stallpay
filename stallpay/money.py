"""Naira and USD helpers. Amounts are Decimal throughout."""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

NGN_QUANT = Decimal("0.01")
USD_QUANT = Decimal("0.01")
KOBO_TOLERANCE = Decimal("1.00")  # ₦1.00 slack on the stated total

_AMOUNT_RE = re.compile(r"[₦N]?\s*([\d,]+(?:\.\d{1,2})?)")


def parse_amount(raw: str | int | float | Decimal | None) -> Decimal | None:
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return raw.quantize(NGN_QUANT)
    if isinstance(raw, (int, float)):
        return Decimal(str(raw)).quantize(NGN_QUANT)
    text = str(raw).strip()
    if not text:
        return None
    cleaned = text.replace(",", "").replace("₦", "").replace("NGN", "").replace("naira", "")
    cleaned = cleaned.replace("USD", "").replace("$", "").strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned):
        match = _AMOUNT_RE.search(text)
        if not match:
            return None
        cleaned = match.group(1).replace(",", "")
    try:
        return Decimal(cleaned).quantize(NGN_QUANT)
    except Exception:
        return None


def money(value: Decimal, quant: Decimal = NGN_QUANT) -> Decimal:
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def format_ngn(value: Decimal) -> str:
    quantized = money(value, NGN_QUANT)
    sign = "-" if quantized < 0 else ""
    body = f"{abs(quantized):,.2f}"
    return f"{sign}₦{body}"


def format_usd(value: Decimal) -> str:
    quantized = money(value, USD_QUANT)
    sign = "-" if quantized < 0 else ""
    return f"{sign}${abs(quantized):,.2f}"


def ngn_to_usd(amount_ngn: Decimal, rate: Decimal) -> Decimal:
    if rate <= 0:
        raise ValueError("Conversion rate must be positive")
    return money(amount_ngn / rate, USD_QUANT)
