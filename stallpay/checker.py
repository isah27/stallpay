"""Deterministic checks that must pass before any PayPal call."""
from __future__ import annotations

import re
from decimal import Decimal

from . import config
from .models import CheckResult, ConvertedLine, ProposedOrder
from .money import NGN_QUANT, USD_QUANT, money, to_usd, tolerance_for

EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)
INSTRUCTION_RE = re.compile(
    r"\b(ignore (previous|all) instructions|skip the checker|mark this (order )?paid|"
    r"you are now|system prompt|ignore the floor|desobedece el piso|"
    r"floor price ko ignore)\b",
    re.IGNORECASE,
)


def check_order(
    order: ProposedOrder,
    rate: Decimal | None = None,
    rate_as_of: str | None = None,
    floor_total: Decimal | None = None,
    required_total: Decimal | None = None,
    require_agreement: bool = False,
    buyer_messages: list[str] | None = None,
    seller_messages: list[str] | None = None,
) -> CheckResult:
    currency = (order.currency or "NGN").upper()
    try:
        rate = rate if rate is not None else config.rate_for(currency)
    except ValueError as exc:
        rate = Decimal("0")
        rate_error = str(exc)
    else:
        rate_error = ""
    rate_as_of = rate_as_of if rate_as_of is not None else config.RATE_AS_OF
    errors: list[str] = []
    warnings: list[str] = []
    if rate_error:
        errors.append(rate_error)

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

    if rate <= 0 and not rate_error:
        errors.append("The currency-to-USD conversion rate must be a positive number.")

    for index, item in enumerate(order.items, start=1):
        label = item.name.strip() or f"item {index}"
        if not item.name.strip():
            errors.append(f"Line {index} is missing a name.")
        if item.quantity <= 0:
            errors.append(f"{label}: quantity must be greater than zero (got {item.quantity}).")
        if item.unit_price_ngn <= 0:
            errors.append(
                f"{label}: unit price must be greater than zero (got {money(item.unit_price_ngn)} {currency})."
            )
        line_total = money(item.quantity * item.unit_price_ngn, NGN_QUANT)
        computed += line_total
        unit_usd = Decimal("0.00")
        line_usd = Decimal("0.00")
        if rate > 0 and item.unit_price_ngn > 0:
            unit_usd = to_usd(item.unit_price_ngn, rate)
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
                currency=currency,
            )
        )

    computed = money(computed, NGN_QUANT)
    usd_total = money(sum((row.line_total_usd for row in usd_items), Decimal("0.00")), USD_QUANT)
    slack = tolerance_for(currency)

    if order.stated_total_ngn is None:
        errors.append("No stated total was found, so the line items cannot be checked.")
    else:
        delta = abs(computed - order.stated_total_ngn)
        if delta > slack:
            errors.append(
                f"Stated total {money(order.stated_total_ngn)} {currency} does not match the computed "
                f"line total {computed} {currency} (difference {money(delta)})."
            )
        elif delta > 0:
            warnings.append(
                f"Stated total and computed total differ by {money(delta)} {currency}, "
                f"within the {slack} {currency} tolerance."
            )

    catalog_total = required_total if required_total is not None else floor_total
    floor_held = True
    if catalog_total is not None:
        agreed = order.stated_total_ngn if order.stated_total_ngn is not None else computed
        expected = money(catalog_total)
        if required_total is not None:
            if abs(agreed - expected) > slack:
                floor_held = False
                errors.append(
                    f"Agreed price {money(agreed)} {currency} does not match the listed or "
                    f"promo price of {expected} {currency}. No invoice will be created."
                )
        elif agreed < expected:
            floor_held = False
            errors.append(
                f"Agreed price {money(agreed)} {currency} is below the seller's floor of "
                f"{expected} {currency}. No invoice will be created."
            )

    if require_agreement:
        _check_agreement(order, computed, buyer_messages, seller_messages, errors)

    haystack = " ".join([order.raw_text or "", order.notes or "", order.agreement_quote or ""])
    if INSTRUCTION_RE.search(haystack):
        warnings.append(
            "The chat contains instruction-like text. StallPay treats the message as data only "
            "and will not follow orders such as 'skip the checker', 'ignore the floor', or 'mark this paid'."
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
        currency=currency,
        floor_total=floor_total,
        floor_held=floor_held,
        agreement_quote=order.agreement_quote or "",
    )


def _check_agreement(
    order: ProposedOrder,
    computed: Decimal,
    buyer_messages: list[str] | None,
    seller_messages: list[str] | None,
    errors: list[str],
) -> None:
    quote = (order.agreement_quote or "").strip()
    speaker = (order.agreement_speaker or "").strip().lower()
    if not quote:
        errors.append("No quoted buyer agreement was found, so a PayPal invoice cannot be created.")
        return
    if speaker and speaker != "buyer":
        errors.append("The agreement quote is not from a buyer message.")
        return
    buyers = buyer_messages if buyer_messages is not None else _buyer_lines(order.raw_text or "")
    sellers = seller_messages or []
    in_buyer = any(_contains_quote(message, quote) for message in buyers)
    in_seller_only = (not in_buyer) and any(_contains_quote(message, quote) for message in sellers)
    if in_seller_only or (buyers and not in_buyer):
        errors.append("The agreement quote is not from a buyer message.")
        return
    if buyers is not None and not buyers and not in_buyer:
        # Fall back: the quote must look like a buyer yes if we have no split transcript.
        pass
    quoted_total = _quoted_amount_matching(quote, order.stated_total_ngn, computed)
    if quoted_total is None:
        # A clear yes with no amount still counts when a single catalog price
        # is already on the order and the quote came from the buyer.
        if parse_amounts_in_quote(quote):
            errors.append(
                "The quoted buyer message does not agree to the exact price of this order."
            )
            return
        quoted_total = money(order.stated_total_ngn if order.stated_total_ngn is not None else computed)
    if order.stated_total_ngn is not None and abs(quoted_total - money(order.stated_total_ngn)) > tolerance_for(order.currency):
        errors.append("The buyer agreed to a different price than the stated order total.")
        return
    if not _quote_covers_items(quote, order):
        errors.append("The quoted buyer message does not agree to the exact items of this order.")


def _buyer_lines(raw_text: str) -> list[str]:
    lines = []
    for line in (raw_text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Heuristic: many pasted chats are "Name: message". We cannot reliably
        # know who the buyer is here, so agreement checks on pasted chats stay optional.
        lines.append(stripped)
    return lines


def _contains_quote(message: str, quote: str) -> bool:
    if not quote.strip():
        return False
    return _norm_text(quote) in _norm_text(message)


def _norm_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _quoted_amount_matching(quote: str, stated: Decimal | None, computed: Decimal) -> Decimal | None:
    from .money import parse_amounts

    targets = [value for value in (stated, computed) if value is not None]
    amounts = parse_amounts(quote)
    for amount in amounts:
        for target in targets:
            if abs(amount - money(target)) <= Decimal("0.05") or amount == money(target):
                return amount
    return None


def _quote_covers_items(quote: str, order: ProposedOrder) -> bool:
    lowered = _norm_text(quote)
    mentioned = 0
    for item in order.items:
        token = _norm_text(item.name)
        if not token:
            continue
        stem = token.rstrip("s")
        if token in lowered or (len(stem) > 3 and stem in lowered):
            mentioned += 1
    if mentioned == len(order.items):
        return True
    others = (
        "leather cuff", "leather cuff (brazalete)", "brazalete de cuero", "brazalete",
        "native shirt", "ankara", "gele (headwrap)", "gele", "headwrap",
        "block-print scarf", "block-print scarf (dupatta)", "scarf", "dupatta",
        "cotton stole", "stole", "aretes de aro", "aretes",
        "silver hoop earrings", "silver hoop earrings (aretes)", "earrings",
    )
    ordered_names = " ".join(_norm_text(item.name) for item in order.items)
    named_other = any(other in lowered and other not in ordered_names for other in others)
    if named_other:
        return False
    # A price-only yes is accepted only for a single item already on the table.
    return len(order.items) == 1


def parse_amounts_in_quote(quote: str) -> list:
    from .money import parse_amounts

    amounts = parse_amounts(quote)
    return [amount for amount in amounts if amount > 20]
