"""StallPay web app: a global chat sales agent with a checked PayPal invoice."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, db, limits, webhooks
from .agent import get_session, handle_buyer_message, start_session
from .eval_scripts import evaluate_all
from .models import ProposedOrder
from .paypal.factory import make_paypal_client
from .paypal.mock import MockPaypalClient
from .samples import SAMPLES, public_sample
from .services import (
    create_and_send,
    create_from_session,
    evaluate_full,
    evaluate_proof_for_invoice,
    evaluate_samples,
    preview_order,
    preview_text,
    refresh_invoice,
    remind_invoice,
    sample_text,
    seller_briefing,
)
from .shops import list_shops

APP_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="StallPay", version="0.2.0", lifespan=lifespan)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


@app.middleware("http")
async def usage_visitor_middleware(request: Request, call_next):
    limits.clear_notice()
    cookie, _ip, is_new = limits.bind_request(request)
    try:
        response = await call_next(request)
        limits.attach_cookie(response, cookie, is_new)
        return response
    finally:
        limits.clear_visitor()


def _client():
    return make_paypal_client()


def _metrics_payload() -> dict:
    data = evaluate_full()
    v1 = data.get("v1_regression") or {}
    # Keep the original top-level keys so existing tests and links still work.
    for key, value in v1.items():
        data.setdefault(key, value)
    return data


def _page_context(request: Request, **extra):
    metrics = evaluate_samples()
    full = _metrics_payload()
    ctx = {
        "request": request,
        "samples": [public_sample(s) for s in SAMPLES if s["category"] == "success"],
        "failures": [public_sample(s) for s in SAMPLES if s["category"] == "failure"],
        "shops": [shop.to_public() for shop in list_shops()],
        "paypal_mode": "live" if config.paypal_is_live() else "mock",
        "llm_configured": config.LLM_AVAILABLE,
        "rate": str(config.NGN_PER_USD),
        "mxn_rate": str(config.MXN_PER_USD),
        "inr_rate": str(config.INR_PER_USD),
        "rate_as_of": config.RATE_AS_OF,
        "metrics": metrics,
        "full_metrics": full,
        "invoices": [_board_row(row) for row in db.list_invoices()],
    }
    ctx.update(extra)
    return ctx


def _board_row(row: dict) -> dict:
    return webhooks._public(row)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "paypal_mode": "live" if config.paypal_is_live() else "mock",
        "llm_configured": config.LLM_AVAILABLE,
    }


@app.get("/metrics")
def metrics(request: Request, format: str | None = None):
    data = _metrics_payload()
    if format == "json" or (request.headers.get("accept") or "").startswith("application/json"):
        return JSONResponse(data)
    return templates.TemplateResponse(request, "metrics.html", {"metrics": data, "full_metrics": data})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", _page_context(request))


@app.get("/api/samples")
def api_samples():
    return [public_sample(s) for s in SAMPLES]


@app.get("/api/shops")
def api_shops():
    return [shop.to_public() for shop in list_shops()]


@app.get("/api/invoices")
def api_invoices():
    return [_board_row(row) for row in db.list_invoices()]


@app.get("/api/briefing")
def api_briefing():
    return seller_briefing()


@app.post("/api/chats")
async def api_start_chat(request: Request):
    body = await request.json()
    shop_id = str(body.get("shop_id") or "").strip()
    try:
        session = start_session(shop_id, body.get("language"))
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown shop")
    if body.get("buyer_name"):
        session.buyer_name = str(body["buyer_name"]).strip()
    if body.get("buyer_email"):
        session.buyer_email = str(body["buyer_email"]).strip()
    return session.to_public()


@app.post("/api/chats/{session_id}/messages")
async def api_chat_message(session_id: str, request: Request):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown chat session")
    body = await request.json()
    text = str(body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Type a buyer message.")
    if body.get("buyer_name"):
        session.buyer_name = str(body["buyer_name"]).strip()
    if body.get("buyer_email"):
        session.buyer_email = str(body["buyer_email"]).strip()
    try:
        result = handle_buyer_message(session, text, prefer_llm=bool(body.get("prefer_llm", True)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@app.post("/api/chats/{session_id}/invoice")
async def api_chat_invoice(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown chat session")
    result = create_from_session(session, _client())
    status = 201 if result.get("ok") else (422 if result.get("blocked") else 502)
    return JSONResponse(result, status_code=status)


@app.post("/api/invoices/{pk}/proof")
async def api_proof(
    pk: int,
    request: Request,
    text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
):
    content_type = request.headers.get("content-type") or ""
    image_bytes = None
    mime = "image/png"
    if "application/json" in content_type:
        body = await request.json()
        text = str(body.get("text") or "")
        prefer_llm = bool(body.get("prefer_llm", True))
    else:
        prefer_llm = True
        if image is not None:
            mime = image.content_type or "image/png"
            image_bytes = await image.read()
            if len(image_bytes) > 4_000_000:
                raise HTTPException(status_code=400, detail="The image is too large.")
    try:
        result = evaluate_proof_for_invoice(
            pk,
            _client(),
            text=text,
            image_bytes=image_bytes,
            mime=mime,
            prefer_llm=prefer_llm,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Invoice not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@app.post("/api/preview")
async def api_preview(request: Request):
    body = await request.json()
    if body.get("sample_id") and not body.get("text") and not body.get("order"):
        text = sample_text(str(body["sample_id"]))
        if not text:
            raise HTTPException(status_code=404, detail="Unknown sample")
        return preview_text(text, prefer_llm=bool(body.get("prefer_llm", True)))
    if body.get("order"):
        order = ProposedOrder.from_dict(body["order"])
        if body.get("raw_text"):
            order.raw_text = body["raw_text"]
        return preview_order(order)
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Paste an order or choose a sample.")
    return preview_text(text, prefer_llm=bool(body.get("prefer_llm", True)), currency=body.get("currency"))


@app.post("/api/invoices")
async def api_create_invoice(request: Request):
    body = await request.json()
    if body.get("order"):
        order = ProposedOrder.from_dict(body["order"])
        order.raw_text = body.get("raw_text") or order.raw_text
    else:
        text = (body.get("text") or "").strip()
        if body.get("sample_id") and not text:
            text = sample_text(str(body["sample_id"])) or ""
        if not text:
            raise HTTPException(status_code=400, detail="Paste an order or provide a checked draft.")
        preview = preview_text(text)
        if preview["blocked"]:
            return JSONResponse({**preview, "ok": False}, status_code=422)
        order = ProposedOrder.from_dict(preview["order"])
    result = create_and_send(order, _client())
    status = 201 if result.get("ok") else (422 if result.get("blocked") else 502)
    return JSONResponse(result, status_code=status)


@app.post("/api/invoices/{pk}/refresh")
def api_refresh(pk: int):
    try:
        return refresh_invoice(pk, _client())
    except KeyError:
        raise HTTPException(status_code=404, detail="Invoice not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/invoices/{pk}/remind")
def api_remind(pk: int):
    try:
        return remind_invoice(pk, _client())
    except KeyError:
        raise HTTPException(status_code=404, detail="Invoice not found")
    except (ValueError, Exception) as exc:
        message = str(exc)
        raise HTTPException(status_code=400, detail=message)


@app.post("/webhooks/paypal")
async def paypal_webhook(request: Request):
    body = await request.body()
    try:
        event = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    headers = {k: v for k, v in request.headers.items()}
    client = _client()
    verified = False
    if isinstance(client, MockPaypalClient):
        verified = client.verify_webhook(headers, body, event)
    else:
        verified = client.verify_webhook(headers, body, event)
        if not verified and not config.PAYPAL_WEBHOOK_ID.strip():
            # Signature verification is not configured. We still accept the event
            # only as a hint; the Refresh button confirms status with GET invoice.
            event["_unverified"] = True
            verified = True
        elif not verified:
            raise HTTPException(status_code=400, detail="Webhook signature check failed")
    if not verified:
        raise HTTPException(status_code=400, detail="Webhook rejected")
    result = webhooks.handle_webhook_event(event)
    return result


@app.get("/mock-pay/{invoice_id}", response_class=HTMLResponse)
def mock_pay_page(request: Request, invoice_id: str):
    client = _client()
    if not isinstance(client, MockPaypalClient):
        raise HTTPException(status_code=404, detail="Mock payment is only available in mock mode.")
    try:
        invoice = client.get_invoice(invoice_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown mock invoice")
    return templates.TemplateResponse(
        request,
        "mock_pay.html",
        {"invoice": invoice.to_dict(), "already_paid": invoice.status == "PAID"},
    )


@app.post("/mock-pay/{invoice_id}")
async def mock_pay_submit(invoice_id: str):
    client = _client()
    if not isinstance(client, MockPaypalClient):
        raise HTTPException(status_code=404, detail="Mock payment is only available in mock mode.")
    try:
        invoice = client.mark_paid(invoice_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown mock invoice")
    event = {
        "event_source": "stallpay-mock",
        "event_type": "INVOICING.INVOICE.PAID",
        "resource": {"id": invoice.invoice_id, "status": "PAID"},
    }
    webhooks.handle_webhook_event(event)
    return {"ok": True, "invoice": invoice.to_dict()}
