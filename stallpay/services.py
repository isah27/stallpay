"""Application services: extract, check, create invoice, evaluate samples."""
from __future__ import annotations

from typing import Any

from . import config, db
from .agent import ChatSession, close_if_agreed, maybe_build_order
from .briefing import draft_remind_note, morning_briefing
from .checker import check_order
from .eval_scripts import evaluate_all
from .extractors import HeuristicExtractor, make_extractor
from .models import ProposedOrder
from .money import format_money
from .paypal.live import PaypalApiError
from .limits import attach_usage_note
from .proof import check_proof, get_invoice_safe, propose_from_image, propose_from_text
from .samples import SAMPLES, get_sample
from .webhooks import _public, map_paypal_status, refresh_from_paypal

INVOICE_NOTE_TEMPLATE = (
    "Original prices in {currency}. PayPal collects USD using a fixed demo "
    "conversion of 1 USD = {rate} {currency}, dated {rate_as_of}. Sandbox only — not a live payment. "
    "Computed {currency} total: {local}."
)


def preview_text(text: str, prefer_llm: bool = True, currency: str | None = None) -> dict[str, Any]:
    extractor = make_extractor(prefer_llm=prefer_llm)
    order = extractor.extract(text)
    if currency:
        order.currency = currency.upper()
    check = check_order(order)
    return attach_usage_note({
        "order": order.to_dict(),
        "check": check.to_dict(),
        "extractor": extractor.name if prefer_llm and config.LLM_AVAILABLE else order.source,
        "blocked": not check.ok,
    })


def preview_order(order: ProposedOrder) -> dict[str, Any]:
    check = check_order(order)
    return {
        "order": order.to_dict(),
        "check": check.to_dict(),
        "extractor": order.source or "manual",
        "blocked": not check.ok,
    }


def _invoice_note(order: ProposedOrder, check) -> str:
    currency = (check.currency or order.currency or "NGN").upper()
    return INVOICE_NOTE_TEMPLATE.format(
        currency=currency,
        rate=f"{check.rate:.2f}",
        rate_as_of=check.rate_as_of,
        local=format_money(check.computed_total_ngn, currency),
    )


def create_and_send(
    order: ProposedOrder,
    client,
    *,
    floor_total=None,
    require_agreement: bool = False,
    buyer_messages: list[str] | None = None,
    seller_messages: list[str] | None = None,
    shop_id: str | None = None,
) -> dict[str, Any]:
    check = check_order(
        order,
        floor_total=floor_total,
        require_agreement=require_agreement,
        buyer_messages=buyer_messages,
        seller_messages=seller_messages,
    )
    if not check.ok:
        return {"ok": False, "blocked": True, "order": order.to_dict(), "check": check.to_dict()}
    note = _invoice_note(order, check)
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
            "shop_id": shop_id or "",
        }
    )
    return {"ok": True, "blocked": False, "invoice": _public(record), "order": order.to_dict(), "check": check.to_dict()}


def create_from_session(session: ChatSession, client) -> dict[str, Any]:
    close = close_if_agreed(session)
    if not close["ready"]:
        check = close.get("check")
        order = close.get("order")
        return {
            "ok": False,
            "blocked": True,
            "reason": close.get("reason") or "The checker did not accept this close.",
            "order": None if order is None else order.to_dict(),
            "check": None if check is None else check.to_dict(),
            "session": session.to_public(),
        }
    result = create_and_send(
        close["order"],
        client,
        floor_total=session.floor_total(),
        require_agreement=True,
        buyer_messages=session.buyer_messages(),
        seller_messages=session.seller_messages(),
        shop_id=session.shop_id,
    )
    if result.get("ok"):
        session.closed = True
        session.invoice_pk = result["invoice"]["id"]
        session.paypal_invoice_id = result["invoice"]["paypal_invoice_id"]
        result["session"] = session.to_public()
    else:
        result["session"] = session.to_public()
    return result


def remind_invoice(pk: int, client) -> dict[str, Any]:
    record = db.get_invoice_by_pk(pk)
    if not record:
        raise KeyError("Invoice not found")
    if record["status"] in {"paid", "cancelled", "refunded"}:
        raise ValueError(f"Cannot remind an invoice that is already {record['status']}.")
    paypal_id = record.get("paypal_invoice_id")
    if not paypal_id:
        raise ValueError("This row has no PayPal invoice id.")
    note = draft_remind_note(record)
    client.remind(paypal_id, note=note)
    updated = db.update_invoice(pk, reminder_sent=True, notes=(record.get("notes") or "") + "\nREMIND: " + note)
    public = _public(updated or record)
    public["remind_note"] = note
    return public


def refresh_invoice(pk: int, client) -> dict[str, Any]:
    record = db.get_invoice_by_pk(pk)
    if not record:
        raise KeyError("Invoice not found")
    updated = refresh_from_paypal(record, client)
    return _public(updated)


def evaluate_proof_for_invoice(
    pk: int,
    client,
    *,
    text: str = "",
    image_bytes: bytes | None = None,
    mime: str = "image/png",
    prefer_llm: bool = True,
) -> dict[str, Any]:
    record = db.get_invoice_by_pk(pk)
    if not record:
        raise KeyError("Invoice not found")
    paypal_id = record.get("paypal_invoice_id")
    if not paypal_id:
        raise ValueError("This row has no PayPal invoice id.")
    if image_bytes:
        proposal = propose_from_image(image_bytes, mime, caption=text, prefer_llm=prefer_llm)
    else:
        proposal = propose_from_text(text, prefer_llm=prefer_llm)
    invoice, error = get_invoice_safe(client, paypal_id)
    if invoice is None:
        result = {
            "verdict": "unverified_waiting_for_paypal",
            "reasons": [error or "PayPal invoice could not be loaded."],
            "proposal": proposal.to_dict(),
            "paypal_status": None,
            "paypal_invoice_id": paypal_id,
            "paypal_amount_usd": None,
            "marks_paid": False,
            "summary": "Unverified, waiting for PayPal.",
        }
    else:
        result = check_proof(proposal, invoice, record)
    result["invoice"] = _public(record)
    # The image itself never flips the board to Paid.
    result["marks_paid"] = False
    return attach_usage_note(result)


def seller_briefing() -> dict[str, Any]:
    return morning_briefing([_public(row) for row in db.list_invoices()])


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
    base = {
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
            "mxn_per_usd": str(config.MXN_PER_USD),
            "inr_per_usd": str(config.INR_PER_USD),
            "rate_as_of": config.RATE_AS_OF,
        },
    }
    return base


def evaluate_full() -> dict[str, Any]:
    return evaluate_all(evaluate_samples())


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
