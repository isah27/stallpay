"""Currency helpers. Amounts are Decimal throughout.

Historical field names such as unit_price_ngn still mean "amount in the
seller's currency" when that currency is naira, and stay in place so the
original sample tests keep working. Newer code should use format_money and
to_usd with an explicit currency code.
"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

NGN_QUANT = Decimal("0.01")
USD_QUANT = Decimal("0.01")
KOBO_TOLERANCE = Decimal("1.00")  # ₦1.00 slack on a stated naira total

CURRENCY_QUANT = Decimal("0.01")

SYMBOLS = {
    "NGN": "₦",
    "USD": "$",
    "MXN": "MX$",
    "INR": "₹",
}

# Named, dated demo tolerances on the stated seller-currency total.
TOLERANCE = {
    "NGN": Decimal("1.00"),
    "MXN": Decimal("1.00"),
    "INR": Decimal("1.00"),
    "USD": Decimal("0.05"),
}

_AMOUNT_RE = re.compile(
    r"(?:₦|NGN|MX\$|MXN|₹|Rs\.?|INR|USD|\$|pesos?|rupees?)?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


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
    cleaned = text.replace(",", "")
    for token in ("₦", "NGN", "naira", "USD", "$", "MX$", "MXN", "pesos", "peso", "₹", "INR", "Rs.", "Rs", "rupees", "rupee"):
        cleaned = re.sub(re.escape(token), "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
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
    return format_money(value, "NGN")


def format_usd(value: Decimal) -> str:
    return format_money(value, "USD")


def format_money(value: Decimal, currency: str = "NGN") -> str:
    code = (currency or "NGN").upper()
    quantized = money(value, CURRENCY_QUANT)
    sign = "-" if quantized < 0 else ""
    body = f"{abs(quantized):,.2f}"
    symbol = SYMBOLS.get(code, f"{code} ")
    if code in {"NGN", "USD", "MXN", "INR"}:
        return f"{sign}{symbol}{body}"
    return f"{sign}{body} {code}"


def ngn_to_usd(amount_ngn: Decimal, rate: Decimal) -> Decimal:
    return to_usd(amount_ngn, rate)


def to_usd(amount: Decimal, rate: Decimal) -> Decimal:
    if rate <= 0:
        raise ValueError("Conversion rate must be positive")
    return money(amount / rate, USD_QUANT)


def tolerance_for(currency: str) -> Decimal:
    return TOLERANCE.get((currency or "NGN").upper(), Decimal("1.00"))


def parse_amounts(text: str) -> list[Decimal]:
    found: list[Decimal] = []
    for match in _AMOUNT_RE.finditer(text or ""):
        value = parse_amount(match.group(1))
        if value is not None:
            found.append(value)
    return found
