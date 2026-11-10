from decimal import Decimal

from stallpay.agent import close_if_agreed, handle_buyer_message, reset_sessions, start_session
from stallpay.eval_scripts import run_agreement_suite, run_price_suite, run_promo_expiry_suite, run_proof_suite
from stallpay.money import format_money, money, to_usd
from stallpay.shops import get_shop


def setup_function():
    reset_sessions()


def test_currency_formatting_and_conversion():
    assert format_money(Decimal("850"), "MXN").startswith("MX$")
    assert format_money(Decimal("1800"), "INR").startswith("₹")
    assert to_usd(Decimal("1820"), Decimal("18.20")) == Decimal("100.00")


def test_price_scripts_all_hold():
    result = run_price_suite()
    assert result["held"] == result["total"] == 15, result["misses"]
    assert result["misses"] == []


def test_promo_expiry_is_respected():
    result = run_promo_expiry_suite()
    assert result["held"] == result["total"], result["misses"]
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


def test_live_shop_quotes_promo_then_accepts_clear_yes():
    session = start_session("mexico")
    handle_buyer_message(session, "Quiero los aretes de aro de plata.", prefer_llm=False)
    expected = get_shop("mexico").item("earrings").selling_price()
    assert session.quoted_price == money(expected)
    handle_buyer_message(session, "Te doy 300 pesos.", prefer_llm=False)
    assert session.quoted_price == money(expected)
    assert close_if_agreed(session)["ready"] is False
    handle_buyer_message(session, "De acuerdo, lo tomo.", prefer_llm=False)
    close = close_if_agreed(session)
    assert close["ready"] is True
    assert close["check"].ok
    assert close["order"].currency == "MXN"
    assert close["order"].stated_total_ngn == money(expected)
    assert close["order"].agreement_quote


def test_pidgin_and_hindi_bargains_keep_catalog_price():
    cases = (
        ("lagos", "Abeg I wan one native shirt.", "I go pay ₦5,000 only.", "native-shirt"),
        ("jaipur", "Block-print scarf chahiye.", "Main 200 rupaye dunga.", "scarf"),
    )
    for shop_id, message, follow, item_id in cases:
        reset_sessions()
        session = start_session(shop_id)
        handle_buyer_message(session, message, prefer_llm=False)
        handle_buyer_message(session, follow, prefer_llm=False)
        expected = get_shop(shop_id).item(item_id).selling_price()
        assert session.quoted_price == money(expected), shop_id
