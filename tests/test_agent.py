from decimal import Decimal

from stallpay.agent import close_if_agreed, handle_buyer_message, reset_sessions, start_session
from stallpay.eval_scripts import run_agreement_suite, run_floor_suite, run_proof_suite
from stallpay.money import format_money, money, to_usd


def setup_function():
    reset_sessions()


def test_currency_formatting_and_conversion():
    assert format_money(Decimal("850"), "MXN").startswith("MX$")
    assert format_money(Decimal("1800"), "INR").startswith("₹")
    assert to_usd(Decimal("1820"), Decimal("18.20")) == Decimal("100.00")


def test_floor_scripts_all_hold():
    result = run_floor_suite()
    assert result["held"] == result["total"] == 15, result["misses"]
    assert result["misses"] == []


def test_agreement_gate_false_invoice_rate_is_zero():
    result = run_agreement_suite()
    assert result["false_invoice_count"] == 0, result["rows"]
    priced = next(row for row in result["rows"] if row["id"] == "priced_yes")
    assert priced["would_invoice"] is True
    assert result["pass_count"] == result["total"]


def test_proof_fixtures():
    result = run_proof_suite()
    assert result["fake_caught"] == result["fake_total"]
    assert result["genuine_confirmed"] == result["genuine_total"]
    assert result["genuine_false_alarms"] == 0
    assert all(not row["marks_paid"] for row in result["rows"])
    assert all(row["pass"] for row in result["rows"])


def test_live_haggle_holds_floor_then_accepts_priced_yes():
    session = start_session("mexico")
    handle_buyer_message(session, "Quiero los aretes de aro de plata.", prefer_llm=False)
    handle_buyer_message(session, "Te doy 300 pesos.", prefer_llm=False)
    assert session.current_offer is not None
    assert session.current_offer >= session.floor_total()
    assert session.current_offer >= Decimal("720")
    # Not closed yet
    assert close_if_agreed(session)["ready"] is False
    offer = session.current_offer
    handle_buyer_message(session, f"De acuerdo, lo tomo a MX${offer}.", prefer_llm=False)
    close = close_if_agreed(session)
    assert close["ready"] is True
    assert close["check"].ok
    assert close["order"].currency == "MXN"
    assert close["order"].agreement_quote


def test_pidgin_and_hindi_lowballs_hold():
    for shop_id, message, follow in (
        ("lagos", "Abeg I wan one native shirt.", "I go pay ₦5,000 only."),
        ("jaipur", "Block-print scarf chahiye.", "Main 200 rupaye dunga."),
    ):
        reset_sessions()
        session = start_session(shop_id)
        handle_buyer_message(session, message, prefer_llm=False)
        handle_buyer_message(session, follow, prefer_llm=False)
        assert session.current_offer >= session.floor_total(), shop_id
