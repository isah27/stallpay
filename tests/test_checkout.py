from stallpay.money import money, to_usd
from stallpay import config
from stallpay.paypal import mock as mock_mod
from stallpay.shops import get_shop


def test_home_has_summary_card_and_no_receipt_upload(client):
    home = client.get("/").text
    assert 'id="order-card"' in home
    assert "Proceed with PayPal" in home
    assert "I've already paid" in home
    assert "proof-panel" not in home
    assert 'id="proof-file"' not in home
    assert "Paste your receipt" not in home
    assert 'id="lang-select"' in home


def _agree_mexico(client):
    started = client.post("/api/chats", json={"shop_id": "mexico"}).json()
    sid = started["id"]
    client.post(f"/api/chats/{sid}/messages", json={"text": "I want the earrings", "prefer_llm": False})
    yes = client.post(
        f"/api/chats/{sid}/messages",
        json={"text": "Okay I want it", "prefer_llm": False},
    )
    return yes


def test_agreement_hides_chat_and_returns_order_summary(client):
    yes = _agree_mexico(client)
    body = yes.json()
    assert yes.status_code == 200
    assert body.get("invoiced") is True
    sess = body["session"]
    assert sess.get("pay_url")
    summary = sess["order_summary"]
    assert summary is not None
    shop = get_shop("mexico")
    earrings = shop.item("earrings")
    selling = earrings.selling_price()
    listed = money(earrings.list_price)
    discount = money(listed - selling)
    assert summary["shop_name"] == "Joyería Sofía"
    assert summary["items"][0]["name"] == earrings.name
    assert summary["items"][0]["quantity"] == "1"
    assert summary["list_total"] == str(listed)
    assert summary["promo_discount"] == str(discount)
    assert summary["promo_ends_display"]
    assert summary["total"] == str(selling)
    expected_usd = to_usd(selling, config.rate_for("MXN"))
    assert summary["usd_total"] == str(expected_usd)
    assert "USD" in summary["usd_total_display"] or summary["usd_total_display"].startswith("$")
    assert summary["invoice_number"]
    assert sess["invoice_number"] == summary["invoice_number"]
    # Chat remains in the payload for the seller record, but the pay UI is driven by order_summary.
    assert "paypal-btn" in client.get("/").text


def test_already_paid_maps_unpaid_and_paid_in_mock_mode(client):
    body = _agree_mexico(client).json()
    invoice = body["invoice"]
    pk = invoice["id"]
    paypal_id = invoice["paypal_invoice_id"]
    unpaid = client.post(f"/api/invoices/{pk}/already-paid")
    assert unpaid.status_code == 200
    unpaid_body = unpaid.json()
    assert unpaid_body["paid"] is False
    assert str(unpaid_body["paypal_status"]).upper() not in {"PAID", "MARKED_AS_PAID"}
    assert "hasn't confirmed" in unpaid_body["message"] or "has not" in unpaid_body["message"].lower()

    mock_mod.MockPaypalClient(public_base_url="http://testserver").mark_paid(paypal_id)
    paid = client.post(f"/api/invoices/{pk}/already-paid").json()
    assert paid["paid"] is True
    assert paid["status"] == "paid"
    assert "confirmed" in paid["message"].lower()

    # A second invoice can be confirmed via MARKED_AS_PAID.
    second = _agree_mexico(client).json()
    pk2 = second["invoice"]["id"]
    paypal2 = second["invoice"]["paypal_invoice_id"]
    mock_mod.MockPaypalClient(public_base_url="http://testserver").set_status(paypal2, "MARKED_AS_PAID")
    marked = client.post(f"/api/invoices/{pk2}/already-paid").json()
    assert marked["paid"] is True
    assert str(marked["paypal_status"]).upper() == "MARKED_AS_PAID"
