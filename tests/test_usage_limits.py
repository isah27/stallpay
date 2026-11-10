from __future__ import annotations

import httpx

from stallpay import config, limits
from stallpay.agent import handle_buyer_message, reset_sessions, start_session
from stallpay.limits import USAGE_NOTE
from stallpay.llm_client import LlmCapped, complete, complete_vision
from stallpay.proof import propose_from_text


class _FakeResponse:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


class _FakeClient:
    calls: list[dict] = []
    content = "Normalmente son MX$850, pero con la promo quedan en MX$760. La promo termina el jueves."

    def __init__(self, timeout=None):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, headers=None, json=None):
        # Store only non-secret request fields.
        _FakeClient.calls.append(
            {
                "url_suffix": str(url).rsplit("/", 1)[-1],
                "max_tokens": (json or {}).get("max_tokens"),
                "has_auth": bool(headers and "Authorization" in headers),
            }
        )
        return _FakeResponse(_FakeClient.content)


def _enable_model(monkeypatch, **caps):
    monkeypatch.setattr(config, "LLM_AVAILABLE", True)
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setattr(config, "LLM_MODEL", "demo-model")
    monkeypatch.setattr(config, "LLM_AUTH_SCHEME", "Api-Key")
    monkeypatch.setattr(config, "LLM_VISITOR_DAILY_LIMIT", caps.get("visitor_daily", 200))
    monkeypatch.setattr(config, "LLM_GLOBAL_DAILY_LIMIT", caps.get("global_daily", 3000))
    monkeypatch.setattr(config, "LLM_VISITOR_BURST_PER_MINUTE", caps.get("burst", 30))
    monkeypatch.setattr(config, "LLM_MAX_INPUT_CHARS", caps.get("max_input", 12000))
    monkeypatch.setattr(config, "LLM_MAX_TOKENS", caps.get("max_tokens", 400))
    limits.reset()
    limits.clear_notice()


def setup_function():
    reset_sessions()
    limits.reset()
    limits.clear_notice()
    _FakeClient.calls = []


def test_consume_enforces_visitor_daily_and_ip_and_global(monkeypatch):
    _enable_model(monkeypatch, visitor_daily=2, global_daily=5)
    limits.set_visitor("visitor-aaaaaaaaaaaa", "1.1.1.1")
    assert limits.consume(10) is True
    assert limits.consume(10) is True
    assert limits.consume(10) is False
    assert limits.pop_notice() == USAGE_NOTE

    limits.clear_notice()
    limits.set_visitor("visitor-bbbbbbbbbbbb", "1.1.1.1")
    # Same IP should also be at the per-visitor daily cap.
    assert limits.consume(10) is False

    _enable_model(monkeypatch, visitor_daily=200, global_daily=2)
    limits.set_visitor("visitor-cccccccccccc", "2.2.2.2")
    assert limits.consume(10) is True
    limits.set_visitor("visitor-dddddddddddd", "3.3.3.3")
    assert limits.consume(10) is True
    limits.set_visitor("visitor-eeeeeeeeeeee", "4.4.4.4")
    assert limits.consume(10) is False


def test_consume_enforces_burst_and_input_length(monkeypatch):
    _enable_model(monkeypatch, burst=3, max_input=20)
    limits.set_visitor("visitor-ffffffffffff", "5.5.5.5")
    assert limits.consume(100) is False
    assert limits.pop_notice() == USAGE_NOTE
    limits.clear_notice()
    assert limits.consume(10) is True
    assert limits.consume(10) is True
    assert limits.consume(10) is True
    assert limits.consume(10) is False


def test_complete_respects_cap_and_clamps_max_tokens(monkeypatch):
    _enable_model(monkeypatch, visitor_daily=1, max_tokens=200)
    limits.set_visitor("visitor-gggggggggggg", "6.6.6.6")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    text = complete("sys", "hello", max_tokens=700)
    assert "850" in text
    assert _FakeClient.calls[0]["max_tokens"] == 200
    limits.clear_notice()
    try:
        complete("sys", "again", max_tokens=50)
        assert False, "expected cap"
    except LlmCapped:
        pass
    assert len(_FakeClient.calls) == 1
    assert limits.pop_notice() == USAGE_NOTE


def test_complete_vision_ignores_image_size_for_input_cap(monkeypatch):
    _enable_model(monkeypatch, max_input=30)
    limits.set_visitor("visitor-hhhhhhhhhhhh", "7.7.7.7")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    _FakeClient.content = '{"amount": "12.00"}'
    text = complete_vision("extract", "read this", "a" * 5000)
    assert "12.00" in text
    assert len(_FakeClient.calls) == 1


def test_chat_falls_back_to_scripted_reply_when_capped_and_holds_price(monkeypatch):
    _enable_model(monkeypatch, visitor_daily=0)
    limits.set_visitor("visitor-iiiiiiiiiiii", "8.8.8.8")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    session = start_session("mexico")
    result = handle_buyer_message(session, "Quiero los aretes de aro de plata.", prefer_llm=True)
    assert result["usage_note"] == USAGE_NOTE
    assert _FakeClient.calls == []
    assert session.quoted_price == session.selling_total()
    low = handle_buyer_message(session, "Te doy 300 pesos.", prefer_llm=True)
    assert low["usage_note"] == USAGE_NOTE
    assert session.quoted_price == session.selling_total()
    assert "760" in low["reply"] or "promo" in low["reply"].lower() or "mejor" in low["reply"].lower()


def test_chat_uses_model_reply_when_under_cap(monkeypatch):
    _enable_model(monkeypatch)
    limits.set_visitor("visitor-jjjjjjjjjjjj", "9.9.9.9")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    session = start_session("mexico")
    result = handle_buyer_message(session, "Quiero los aretes de aro de plata.", prefer_llm=True)
    assert "usage_note" not in result
    assert result["reply"] == _FakeClient.content
    assert len(_FakeClient.calls) == 1


def test_proof_parser_fallback_when_capped(monkeypatch):
    _enable_model(monkeypatch, visitor_daily=0)
    limits.set_visitor("visitor-kkkkkkkkkkkk", "10.10.10.10")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    proposal = propose_from_text("Bank alert: paid $12.00 USD, ref INV-9", prefer_llm=True)
    assert _FakeClient.calls == []
    assert proposal.source == "heuristic"
    assert limits.pop_notice() == USAGE_NOTE


def test_api_sets_visitor_cookie_and_returns_usage_note(client, monkeypatch):
    _enable_model(monkeypatch, visitor_daily=1)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    health = client.get("/health")
    assert "stallpay_vid" in health.cookies
    started = client.post("/api/chats", json={"shop_id": "mexico"})
    session_id = started.json()["id"]
    first = client.post(
        f"/api/chats/{session_id}/messages",
        json={"text": "Quiero los aretes de aro de plata."},
    )
    assert first.status_code == 200
    assert "usage_note" not in first.json()
    assert first.json()["reply"] == _FakeClient.content
    second = client.post(
        f"/api/chats/{session_id}/messages",
        json={"text": "Te doy 300 pesos."},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["usage_note"] == USAGE_NOTE
    assert body["reply"] != _FakeClient.content
    assert second.json()["session"]["quoted_price"] == "760.00"
    assert len(_FakeClient.calls) == 1


def test_home_includes_usage_note_placeholder(client):
    html = client.get("/").text
    assert 'id="usage-note"' in html


def test_complete_rejects_empty_content(monkeypatch):
    from stallpay.llm_client import LlmError

    _enable_model(monkeypatch)
    limits.set_visitor("visitor-llllllllllll", "11.11.11.11")
    _FakeClient.content = None
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    try:
        complete("sys", "hello", max_tokens=50)
        assert False, "expected unusable response"
    except LlmError:
        pass
    _FakeClient.content = "   "
    try:
        complete("sys", "hello", max_tokens=50)
        assert False, "expected unusable response"
    except LlmError:
        pass
