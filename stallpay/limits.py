"""In-memory caps for model calls on a single instance.

Visitor identity is a cookie plus the client IP. Counters are not written to disk
and never log keys, cookie values, or IP addresses.
"""
from __future__ import annotations

import secrets
import threading
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from . import config

COOKIE_NAME = "stallpay_vid"
USAGE_NOTE = "Using the standard reply path for now."

_lock = threading.Lock()
_visitor_daily: dict[tuple[str, str], int] = {}
_global_daily: dict[str, int] = {}
_burst: dict[str, list[float]] = {}

_visitor: ContextVar[tuple[str, str] | None] = ContextVar("stallpay_visitor", default=None)
_notice: ContextVar[str | None] = ContextVar("stallpay_usage_notice", default=None)


class LlmCapped(Exception):
    """The model was skipped because a usage cap was reached."""


def reset() -> None:
    with _lock:
        _visitor_daily.clear()
        _global_daily.clear()
        _burst.clear()
    _notice.set(None)


def set_visitor(cookie: str, ip: str) -> None:
    _visitor.set((cookie, ip or "unknown"))


def clear_visitor() -> None:
    _visitor.set(None)


def current_visitor() -> tuple[str, str] | None:
    return _visitor.get()


def clear_notice() -> None:
    _notice.set(None)


def pop_notice() -> str | None:
    note = _notice.get()
    _notice.set(None)
    return note


def mark_notice() -> None:
    _notice.set(USAGE_NOTE)


def attach_usage_note(result: dict[str, Any]) -> dict[str, Any]:
    note = pop_notice()
    if note:
        result["usage_note"] = note
    return result


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _client_ip(request: Any) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    host = getattr(getattr(request, "client", None), "host", None)
    return host or "unknown"


def _valid_vid(value: str) -> bool:
    if not value or len(value) < 16 or len(value) > 64:
        return False
    return all(ch.isalnum() or ch in "-_" for ch in value)


def bind_request(request: Any) -> tuple[str, str, bool]:
    ip = _client_ip(request)
    raw = request.cookies.get(COOKIE_NAME) or ""
    is_new = False
    if not _valid_vid(raw):
        raw = secrets.token_urlsafe(16)
        is_new = True
    set_visitor(raw, ip)
    return raw, ip, is_new


def attach_cookie(response: Any, cookie: str, is_new: bool) -> None:
    if not is_new:
        return
    secure = str(config.PUBLIC_BASE_URL or "").startswith("https://")
    response.set_cookie(
        COOKIE_NAME,
        cookie,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def _prune_locked(today: str) -> None:
    stale_visitors = [key for key in _visitor_daily if key[0] != today]
    for key in stale_visitors:
        _visitor_daily.pop(key, None)
    stale_global = [day for day in _global_daily if day != today]
    for day in stale_global:
        _global_daily.pop(day, None)


def consume(input_chars: int) -> bool:
    """Reserve one model call if under every cap. On reject, set the usage notice."""
    max_input = int(config.LLM_MAX_INPUT_CHARS)
    if input_chars > max_input:
        mark_notice()
        return False

    visitor = _visitor.get()
    day = _today()
    now = time.time()
    visitor_daily = int(config.LLM_VISITOR_DAILY_LIMIT)
    global_daily = int(config.LLM_GLOBAL_DAILY_LIMIT)
    burst_limit = int(config.LLM_VISITOR_BURST_PER_MINUTE)

    keys: list[str] = []
    if visitor:
        cookie, ip = visitor
        if cookie:
            keys.append(f"vid:{cookie}")
        if ip:
            keys.append(f"ip:{ip}")

    with _lock:
        _prune_locked(day)
        if _global_daily.get(day, 0) >= global_daily:
            mark_notice()
            return False
        for key in keys:
            if _visitor_daily.get((day, key), 0) >= visitor_daily:
                mark_notice()
                return False
            stamps = [stamp for stamp in _burst.get(key, []) if now - stamp < 60]
            _burst[key] = stamps
            if len(stamps) >= burst_limit:
                mark_notice()
                return False
        _global_daily[day] = _global_daily.get(day, 0) + 1
        for key in keys:
            _visitor_daily[(day, key)] = _visitor_daily.get((day, key), 0) + 1
            _burst.setdefault(key, []).append(now)
    return True
