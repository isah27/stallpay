"""Deterministic checks that must pass before any PayPal call."""
from __future__ import annotations

import re
from decimal import Decimal

from . import config
from .models import CheckResult, ConvertedLine, ProposedOrder
from .money import KOBO_TOLERANCE, NGN_QUANT, USD_QUANT, money, ngn_to_usd

EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)
INSTRUCTION_RE = re.compile(
    r"\b(ignore (previous|all) instructions|skip the checker|mark this (order )?paid|"
    r"you are now|system prompt)\b",
    re.IGNORECASE,
)


def check_order(order: ProposedOrder, rate: Decimal | None = None, rate_as_of: str | None = None) -> CheckResult:
    rate = rate if rate is not None else config.NGN_PER_USD
    rate_as_of = rate_as_of if rate_as_of is not None else config.RATE_AS_OF
    errors: list[str] = []
    warnings: list[str] = []

    if not order.buyer_name.strip():
        errors.append("Buyer name is missing.")
    if not order.buyer_email.strip():
        errors.append("Buyer email is missing.")
    elif not EMAIL_RE.match(order.buyer_email.strip()):
        errors.append(f"Buyer email {order.buyer_email!r} is not a valid email address.")

    if not order.items:
        errors.append("No line items were found in the order.")

    computed = Decimal("0.00")
    usd_items: list[ConvertedLine] = []
    seen_names: list[str] = []

    if rate <= 0:
        errors.append("The naira-to-USD conversion rate must be a positive number.")

    for index, item in enumerate(order.items, start=1):
        label = item.name.strip() or f"item {index}"
        if not item.name.strip():
            errors.append(f"Line {index} is missing a name.")
        if item.quantity <= 0:
            errors.append(f"{label}: quantity must be greater than zero (got {item.quantity}).")
        if item.unit_price_ngn <= 0:
            errors.append(f"{label}: unit price must be greater than zero (got ₦{item.unit_price_ngn}).")
        line_total = money(item.quantity * item.unit_price_ngn, NGN_QUANT)
        computed += line_total
        unit_usd = Decimal("0.00")
        line_usd = Decimal("0.00")
        if rate > 0 and item.unit_price_ngn > 0:
            unit_usd = ngn_to_usd(item.unit_price_ngn, rate)
            line_usd = money(item.quantity * unit_usd, USD_QUANT)
            if unit_usd <= 0:
                errors.append(f"{label}: converted USD unit price is not a usable amount.")
        usd_items.append(
            ConvertedLine(
                name=item.name.strip() or label,
                quantity=item.quantity,
                unit_price_ngn=item.unit_price_ngn,
                unit_price_usd=unit_usd,
                line_total_ngn=line_total,
                line_total_usd=line_usd,
            )
        )
        seen_names.append(label.lower())

    computed = money(computed, NGN_QUANT)
    usd_total = money(sum((row.line_total_usd for row in usd_items), Decimal("0.00")), USD_QUANT)

    if order.stated_total_ngn is None:
        errors.append("No stated total was found, so the line items cannot be checked.")
    else:
        delta = abs(computed - order.stated_total_ngn)
        if delta > KOBO_TOLERANCE:
            errors.append(
                f"Stated total ₦{money(order.stated_total_ngn)} does not match the computed "
                f"line total ₦{computed} (difference ₦{money(delta)})."
            )
        elif delta > 0:
            warnings.append(
                f"Stated total and computed total differ by ₦{money(delta)}, within the ₦{KOBO_TOLERANCE} tolerance."
            )

    haystack = " ".join([order.raw_text or "", order.notes or ""])
    if INSTRUCTION_RE.search(haystack):
        warnings.append(
            "The chat contains instruction-like text. StallPay treats the message as data only "
            "and will not follow orders such as 'skip the checker' or 'mark this paid'."
        )

    ok = not errors
    return CheckResult(
        ok=ok,
        errors=errors,
        warnings=warnings,
        computed_total_ngn=computed,
        usd_total=usd_total,
        usd_items=usd_items,
        rate=rate,
        rate_as_of=rate_as_of,
    )
