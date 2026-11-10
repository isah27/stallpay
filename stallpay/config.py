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
LLM_MAX_TOKENS = _int_env("LLM_MAX_TOKENS", 400)

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
