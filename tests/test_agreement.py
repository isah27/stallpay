import httpx

from stallpay.agent import close_if_agreed, handle_buyer_message, reset_sessions, start_session
from stallpay.money import money
from stallpay.shops import get_shop

from tests.test_usage_limits import _FakeClient, _enable_model


AFFIRM_PHRASES = [
    "yes",
    "yeah",
    "yep",
    "sure",
    "ok",
    "okay",
    "I'll take it",
    "I want it",
    "I would like to buy it",
    "I'd like to buy",
    "buy it",
    "let's do it",
    "deal",
    "go ahead",
    "proceed",
    "sounds good",
    "confirm",
    "Yes!",
    "YES",
    "sure.",
    "yess",
    "ok?",
    "sí",
    "claro",
    "haan",
    "ha ji",
    "I go buy am",
]

NEGATIVE_PHRASES = [
    "no",
    "not yet",
    "is it available in blue?",
    "yes but cheaper?",
]

PAY_INTENT_PHRASES = [
    "send me the link",
    "I'll pay now",
    "how do I pay",
    "envíame el enlace",
    "abeg send link",
    "give me the link",
]

ODD_AGREE_PHRASES = [
    "wrap it up for me",
    "abeg make I pay",
]


def setup_function():
    reset_sessions()
    _FakeClient.calls = []


def _quote(shop_id="mexico", select="I want the earrings", item_id="earrings"):
    session = start_session(shop_id)
    handle_buyer_message(session, select, prefer_llm=False)
    expected = get_shop(shop_id).item(item_id).selling_price()
    assert session.quoted_price == money(expected)
    assert close_if_agreed(session)["ready"] is False
    return session, money(expected)


def test_natural_affirmatives_after_a_quote_agree_to_the_quoted_price():
    for phrase in AFFIRM_PHRASES:
        reset_sessions()
        session, expected = _quote()
        result = handle_buyer_message(session, phrase, prefer_llm=False)
        close = close_if_agreed(session)
        assert close["ready"] is True, phrase
        assert session.agreement_quote == phrase
        assert session.quoted_price == expected, phrase
        assert close["order"].stated_total_ngn == expected, phrase
        assert result.get("invoice_ready") is True, phrase
        # The quote should ask a natural question, not demand exact wording.
        quote = next(m.text for m in session.messages if m.role == "seller" and m is not session.messages[0])
        assert "Would you like to buy it?" in quote


def test_pay_intent_phrases_agree_only_after_a_quote():
    for phrase in PAY_INTENT_PHRASES:
        reset_sessions()
        session, expected = _quote()
        result = handle_buyer_message(session, phrase, prefer_llm=False)
        close = close_if_agreed(session)
        assert close["ready"] is True, phrase
        assert session.agreement_quote == phrase
        assert session.quoted_price == expected, phrase
        assert close["order"].stated_total_ngn == expected, phrase
        assert result.get("invoice_ready") is True, phrase


def test_pay_intent_does_not_invoice_without_a_pending_quote():
    for phrase in PAY_INTENT_PHRASES:
        reset_sessions()
        session = start_session("mexico")
        result = handle_buyer_message(session, phrase, prefer_llm=False)
        assert close_if_agreed(session)["ready"] is False, phrase
        assert not session.agreement_quote, phrase
        assert not result.get("invoice_ready"), phrase


def test_pay_intent_yes_does_not_call_the_model(monkeypatch):
    import httpx

    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    session, expected = _quote()
    _FakeClient.calls = []
    handle_buyer_message(session, "send me the link", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is True
    assert session.quoted_price == expected
    assert _FakeClient.calls == []


def test_quote_prompt_asks_if_they_would_like_to_buy_it():
    session, _expected = _quote()
    quote = next(m.text for m in session.messages if m.role == "seller" and m is not session.messages[0])
    assert quote.endswith("Would you like to buy it?")


def test_negatives_and_questions_do_not_agree_after_a_quote():
    for phrase in NEGATIVE_PHRASES:
        reset_sessions()
        session, expected = _quote()
        result = handle_buyer_message(session, phrase, prefer_llm=False)
        assert close_if_agreed(session)["ready"] is False, phrase
        assert not session.agreement_quote, phrase
        assert session.quoted_price == expected, phrase
        assert not result.get("invoice_ready"), phrase


def test_nothing_creates_an_invoice_without_a_pending_quote():
    for phrase in ["yes", "sure", "I would like to buy it", "ok", "send me the link"]:
        reset_sessions()
        session = start_session("mexico")
        result = handle_buyer_message(session, phrase, prefer_llm=False)
        assert session.quoted_price is None
        assert close_if_agreed(session)["ready"] is False, phrase
        assert not session.agreement_quote, phrase
        assert not result.get("invoice_ready"), phrase


def test_first_item_choice_quotes_but_does_not_invoice():
    session = start_session("mexico")
    result = handle_buyer_message(session, "I would like to buy the earrings", prefer_llm=False)
    expected = get_shop("mexico").item("earrings").selling_price()
    assert session.quoted_price == money(expected)
    assert close_if_agreed(session)["ready"] is False
    assert not result.get("invoice_ready")
    assert "Would you like to buy it?" in result["reply"]


def test_yes_at_a_different_price_is_blocked():
    session, expected = _quote()
    handle_buyer_message(session, "Yes, I'll pay MX$400 for the earrings.", prefer_llm=False)
    assert close_if_agreed(session)["ready"] is False
    assert session.quoted_price == expected


def test_deterministic_yes_does_not_call_the_model(monkeypatch):
    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    _FakeClient.calls = []
    session, expected = _quote()
    handle_buyer_message(session, "yes", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is True
    assert session.quoted_price == expected
    assert _FakeClient.calls == []


def test_model_can_accept_odd_phrasing_and_still_locks_the_price(monkeypatch):
    _enable_model(monkeypatch, max_tokens=1000)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    for phrase in ODD_AGREE_PHRASES:
        reset_sessions()
        _FakeClient.calls = []
        _FakeClient.content = "agree"
        session, expected = _quote()
        result = handle_buyer_message(session, phrase, prefer_llm=True)
        close = close_if_agreed(session)
        assert close["ready"] is True, phrase
        assert session.agreement_quote == phrase
        assert session.quoted_price == expected, phrase
        assert close["order"].stated_total_ngn == expected, phrase
        assert result.get("invoice_ready") is True, phrase
        assert _FakeClient.calls, phrase
        # After a classified yes, the chat model is not also called.
        assert len(_FakeClient.calls) == 1, phrase
        assert _FakeClient.calls[0]["max_tokens"] >= 512


def test_model_question_or_other_does_not_invoice(monkeypatch):
    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    for label, phrase in (("question", "is it available in blue?"), ("other", "tell me more")):
        reset_sessions()
        _FakeClient.content = label
        session, expected = _quote()
        handle_buyer_message(session, phrase, prefer_llm=True)
        assert close_if_agreed(session)["ready"] is False, phrase
        assert not session.agreement_quote, phrase
        assert session.quoted_price == expected


def test_model_timeout_or_cap_falls_back_to_the_word_list(monkeypatch):
    class _SlowClient(_FakeClient):
        def post(self, url, headers=None, json=None):
            raise httpx.TimeoutException("slow")

    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _SlowClient)
    session, expected = _quote()
    handle_buyer_message(session, "wrap it up for me", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is False
    assert not session.agreement_quote
    assert session.quoted_price == expected

    reset_sessions()
    _enable_model(monkeypatch, visitor_daily=0)
    from stallpay import limits

    limits.set_visitor("visitor-intentcaptest1", "9.9.9.9")
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    _FakeClient.calls = []
    _FakeClient.content = "agree"
    session, expected = _quote()
    handle_buyer_message(session, "wrap it up for me", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is False
    assert not session.agreement_quote
    assert session.quoted_price == expected
    assert _FakeClient.calls == []
    # A listed yes, including a pay-intent line, still works when the model is capped.
    handle_buyer_message(session, "send me the link", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is True
    assert session.quoted_price == expected

def test_freetext_question_keeps_a_tailored_price_locked_reply(monkeypatch):
    import httpx

    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    _FakeClient.calls = []
    _FakeClient.content = "Of course, I'll gift-wrap them for your mum. The promo price is still MX$760.00."
    session, expected = _quote()
    result = handle_buyer_message(session, "Can you gift-wrap them? They're for my mum.", prefer_llm=True)
    assert close_if_agreed(session)["ready"] is False
    assert not session.agreement_quote
    assert session.quoted_price == expected
    assert "gift-wrap" in result["reply"]
    assert "760" in result["reply"]
    assert "Would you like to buy it?" not in result["reply"]
    # A clear question should skip the classifier and make one chat call.
    assert len(_FakeClient.calls) == 1
    assert _FakeClient.calls[0]["max_tokens"] == 200 or _FakeClient.calls[0]["max_tokens"] >= 200


def test_list_price_only_model_reply_is_kept_and_completed(monkeypatch):
    import httpx

    _enable_model(monkeypatch)
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    _FakeClient.content = "Yes, I can gift-wrap them for your mum. They are normally MX$850.00."
    session, expected = _quote()
    result = handle_buyer_message(session, "Can you gift-wrap them? They're for my mum.", prefer_llm=True)
    assert "gift-wrap" in result["reply"]
    assert "850" in result["reply"]
    assert "760" in result["reply"].replace(",", "")
    assert close_if_agreed(session)["ready"] is False
    assert session.quoted_price == expected

