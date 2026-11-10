"""Application services: extract, check, create invoice, evaluate samples."""
from __future__ import annotations

from typing import Any

from . import config, db
from .checker import check_order
from .extractors import HeuristicExtractor, make_extractor
from .models import ProposedOrder
from .paypal.live import PaypalApiError
from .samples import SAMPLES, get_sample
from .webhooks import _public, map_paypal_status, refresh_from_paypal

INVOICE_NOTE_TEMPLATE = (
    "Original prices in Nigerian naira (NGN). PayPal collects USD using a fixed demo "
    "conversion of 1 USD = {rate} NGN, dated {rate_as_of}. Sandbox only — not a live payment. "
    "Computed naira total: {ngn}."
)


def preview_text(text: str, prefer_llm: bool = True) -> dict[str, Any]:
    extractor = make_extractor(prefer_llm=prefer_llm)
    order = extractor.extract(text)
    check = check_order(order)
    return {
        "order": order.to_dict(),
        "check": check.to_dict(),
        "extractor": extractor.name if prefer_llm and config.LLM_AVAILABLE else order.source,
        "blocked": not check.ok,
    }


def preview_order(order: ProposedOrder) -> dict[str, Any]:
    check = check_order(order)
    return {
        "order": order.to_dict(),
        "check": check.to_dict(),
        "extractor": order.source or "manual",
        "blocked": not check.ok,
    }


def create_and_send(order: ProposedOrder, client) -> dict[str, Any]:
    check = check_order(order)
    if not check.ok:
        return {"ok": False, "blocked": True, "order": order.to_dict(), "check": check.to_dict()}
    note = INVOICE_NOTE_TEMPLATE.format(
        rate=f"{check.rate:.2f}",
        rate_as_of=check.rate_as_of,
        ngn=check.computed_total_ngn,
    )
    try:
        created = client.create_invoice(order, check, note)
        sent = client.send_invoice(created.invoice_id)
    except (PaypalApiError, ValueError, KeyError) as exc:
        return {"ok": False, "blocked": False, "error": str(exc), "order": order.to_dict(), "check": check.to_dict()}
    record = db.insert_invoice(
        {
            "buyer_name": order.buyer_name,
            "buyer_email": order.buyer_email,
            "raw_text": order.raw_text,
            "extraction": order.to_dict(),
            "check": check.to_dict(),
            "paypal_invoice_id": sent.invoice_id,
            "status": map_paypal_status(sent.status) if sent.status != "DRAFT" else "sent",
            "pay_url": sent.pay_url,
            "source": order.source,
            "notes": note,
        }
    )
    return {"ok": True, "blocked": False, "invoice": _public(record), "order": order.to_dict(), "check": check.to_dict()}


def remind_invoice(pk: int, client) -> dict[str, Any]:
    record = db.get_invoice_by_pk(pk)
    if not record:
        raise KeyError("Invoice not found")
    if record["status"] in {"paid", "cancelled", "refunded"}:
        raise ValueError(f"Cannot remind an invoice that is already {record['status']}.")
    paypal_id = record.get("paypal_invoice_id")
    if not paypal_id:
        raise ValueError("This row has no PayPal invoice id.")
    client.remind(paypal_id, note="Gentle reminder: your StallPay invoice is still unpaid.")
    updated = db.update_invoice(pk, reminder_sent=True)
    return _public(updated or record)


def refresh_invoice(pk: int, client) -> dict[str, Any]:
    record = db.get_invoice_by_pk(pk)
    if not record:
        raise KeyError("Invoice not found")
    updated = refresh_from_paypal(record, client)
    return _public(updated)


def evaluate_samples(use_llm: bool = False) -> dict[str, Any]:
    extractor = make_extractor(prefer_llm=use_llm)
    # Metrics always also report the heuristic so judges can reproduce without a model key.
    heuristic = HeuristicExtractor()
    rows = []
    success_pass = 0
    success_total = 0
    failure_blocked = 0
    failure_total = 0
    for sample in SAMPLES:
        order = heuristic.extract(sample["text"])
        check = check_order(order)
        expected = sample.get("expected")
        extraction_ok = False
        if sample["category"] == "success" and expected:
            success_total += 1
            extraction_ok = _matches_expected(order, expected)
            if extraction_ok and check.ok:
                success_pass += 1
        else:
            failure_total += 1
            if not check.ok:
                failure_blocked += 1
        rows.append(
            {
                "id": sample["id"],
                "label": sample["label"],
                "category": sample["category"],
                "failure_reason": sample.get("failure_reason"),
                "extraction_ok": extraction_ok if sample["category"] == "success" else None,
                "checker_ok": check.ok,
                "checker_errors": check.errors,
                "buyer_email": order.buyer_email,
                "buyer_name": order.buyer_name,
                "stated_total_ngn": None if order.stated_total_ngn is None else str(order.stated_total_ngn),
                "computed_total_ngn": str(check.computed_total_ngn),
                "item_count": len(order.items),
            }
        )
    return {
        "extractor": heuristic.name,
        "llm_configured": config.LLM_AVAILABLE,
        "success_samples": success_total,
        "success_extracted_and_checked": success_pass,
        "failure_samples": failure_total,
        "failure_blocked_by_checker": failure_blocked,
        "rows": rows,
        "paypal_mode": "live" if config.paypal_is_live() else "mock",
        "conversion": {
            "ngn_per_usd": str(config.NGN_PER_USD),
            "rate_as_of": config.RATE_AS_OF,
        },
    }


def _matches_expected(order: ProposedOrder, expected: dict[str, Any]) -> bool:
    if order.buyer_email.lower() != str(expected["buyer_email"]).lower():
        return False
    if order.buyer_name.strip().lower() != str(expected["buyer_name"]).strip().lower():
        return False
    if order.stated_total_ngn != expected["stated_total_ngn"]:
        return False
    got = [
        (item.name.lower(), item.quantity, item.unit_price_ngn)
        for item in order.items
    ]
    want = [
        (item["name"].lower(), item["quantity"], item["unit_price_ngn"])
        for item in expected["items"]
    ]
    if len(got) != len(want):
        return False
    # Names may be close (jollof vs packs of jollof); compare qty + price first, then loose name.
    remaining = list(want)
    for name, qty, price in got:
        match_index = None
        for index, (wname, wqty, wprice) in enumerate(remaining):
            if qty == wqty and price == wprice and (wname in name or name in wname or name.rstrip("s") == wname.rstrip("s")):
                match_index = index
                break
        if match_index is None:
            return False
        remaining.pop(match_index)
    return True


def sample_text(sample_id: str) -> str | None:
    sample = get_sample(sample_id)
    return None if not sample else sample["text"]
