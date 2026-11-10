"""Runtime configuration from environment variables only. Never log secret values."""
from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, default)
    return value if value is not None else default


def _has_secret(name: str) -> bool:
    return bool(env(name).strip())


def _int_env(name: str, default: int) -> int:
    raw = env(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    raw = env(name, str(default)).strip()
    try:
        return float(raw)
    except ValueError:
        return default


ROOT.mkdir(parents=True, exist_ok=True)

PAYPAL_MODE = env("PAYPAL_MODE", "mock").strip().lower() or "mock"
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = env("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = env("PAYPAL_WEBHOOK_ID")
PAYPAL_API_BASE = env("PAYPAL_API_BASE", "https://api-m.sandbox.paypal.com")
PAYPAL_INVOICER_EMAIL = env("PAYPAL_INVOICER_EMAIL", "seller@stallpay.example")
PAYPAL_INVOICER_BUSINESS_NAME = env("PAYPAL_INVOICER_BUSINESS_NAME", "StallPay Demo Stall")
PAYPAL_INVOICER_GIVEN_NAME = env("PAYPAL_INVOICER_GIVEN_NAME", "Amaka")
PAYPAL_INVOICER_SURNAME = env("PAYPAL_INVOICER_SURNAME", "Okoye")
# Optional default sandbox buyer used only when a demo shop needs an email.
PAYPAL_BUYER_EMAIL = env("PAYPAL_BUYER_EMAIL", "buyer@stallpay.example")
# Optional sandbox Personal buyer password. Shown on the order summary in
# sandbox or mock mode so judges can pay with fake money. Never for production.
PAYPAL_BUYER_PASSWORD = env("PAYPAL_BUYER_PASSWORD")

PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Prefer an explicit LLM_API_KEY; otherwise reuse a Baseten or model key if present.
LLM_API_KEY = env("LLM_API_KEY") or env("BASETEN_API_KEY") or env("MODEL_API_KEY")
LLM_BASE_URL = env("LLM_BASE_URL", "https://inference.baseten.co/v1").rstrip("/")
LLM_MODEL = env("LLM_MODEL", "meta-models/muse-spark-open-1026")
LLM_AUTH_SCHEME = env("LLM_AUTH_SCHEME", "Api-Key")
VISION_MODEL = env("VISION_MODEL", "").strip()
FORCE_HEURISTIC = env("STALLPAY_FORCE_HEURISTIC", "").strip() in {"1", "true", "yes"}
LLM_AVAILABLE = bool(LLM_API_KEY.strip()) and not FORCE_HEURISTIC

# Public-host caps. Generous defaults so judges can test freely.
LLM_VISITOR_DAILY_LIMIT = _int_env("LLM_VISITOR_DAILY_LIMIT", 200)
LLM_GLOBAL_DAILY_LIMIT = _int_env("LLM_GLOBAL_DAILY_LIMIT", 3000)
LLM_VISITOR_BURST_PER_MINUTE = _int_env("LLM_VISITOR_BURST_PER_MINUTE", 30)
LLM_MAX_INPUT_CHARS = _int_env("LLM_MAX_INPUT_CHARS", 12000)
LLM_MAX_TOKENS = _int_env("LLM_MAX_TOKENS", 2000)
# Chat replies fall back to the scripted agent if the model is slower than this.
# muse-spark-1.3 spends several hundred reasoning tokens before visible text,
# so short budgets return empty content. Keep the on-page typing indicator up.
LLM_CHAT_TIMEOUT = _float_env("LLM_CHAT_TIMEOUT", 20.0)
# After a price is quoted, leftover free-text is classified as agree/decline/question/other.
LLM_INTENT_TIMEOUT = _float_env("LLM_INTENT_TIMEOUT", 12.0)

NGN_PER_USD = Decimal(env("NGN_PER_USD", "1480.00"))
MXN_PER_USD = Decimal(env("MXN_PER_USD", "18.20"))
INR_PER_USD = Decimal(env("INR_PER_USD", "83.50"))
RATE_AS_OF = env("RATE_AS_OF", "10 November 2026")

FX_PER_USD: dict[str, Decimal] = {
    "USD": Decimal("1.00"),
    "NGN": NGN_PER_USD,
    "MXN": MXN_PER_USD,
    "INR": INR_PER_USD,
}

DATABASE_PATH = Path(env("DATABASE_PATH", str(ROOT / "data" / "stallpay.db")))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT / DATABASE_PATH


def rate_for(currency: str) -> Decimal:
    code = (currency or "NGN").upper()
    if code not in FX_PER_USD:
        raise ValueError(f"No labelled demo conversion is configured for {code}.")
    return FX_PER_USD[code]


# Live PayPal is used only when explicitly requested *and* credentials are present.
def paypal_is_live() -> bool:
    return PAYPAL_MODE == "live" and _has_secret("PAYPAL_CLIENT_ID") and _has_secret("PAYPAL_CLIENT_SECRET")


def paypal_is_production() -> bool:
    mode = (PAYPAL_MODE or "").strip().lower()
    if mode in {"production", "prod", "live-production"}:
        return True
    base = (PAYPAL_API_BASE or "").strip().lower()
    if "sandbox.paypal.com" in base:
        return False
    if "paypal.com" in base and "sandbox" not in base:
        return True
    return False


def public_sandbox_buyer() -> dict[str, str] | None:
    # Email and password for the on-page sandbox login note, or None to hide it.
    if paypal_is_production():
        return None
    email = (PAYPAL_BUYER_EMAIL or "").strip()
    password = (PAYPAL_BUYER_PASSWORD or "").strip()
    if not email or not password:
        return None
    return {"email": email, "password": password}


def invoice_buyer_email(fallback: str = "buyer@stallpay.example") -> str:
    """Email billed on a sandbox invoice.

    In sandbox or mock mode, prefer the configured PAYPAL_BUYER_EMAIL so the
    PayPal checkout is prefilled with the same test buyer shown on the order
    card. Production keeps the caller fallback (or the placeholder).
    """
    fallback = (fallback or "buyer@stallpay.example").strip() or "buyer@stallpay.example"
    if paypal_is_production():
        return fallback
    email = (PAYPAL_BUYER_EMAIL or "").strip()
    return email or fallback
