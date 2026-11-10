from stallpay.shops import get_shop


def test_shops_and_chat_invoice_and_fake_proof(client):
    shops = client.get("/api/shops").json()
    assert {shop["id"] for shop in shops} == {"lagos", "mexico", "jaipur"}
    started = client.post("/api/chats", json={"shop_id": "jaipur"}).json()
    session_id = started["id"]
    assert started.get("pay_url") in {None, ""}
    client.post(f"/api/chats/{session_id}/messages", json={"text": "Cotton stole dikhao."})
    mid = client.post(f"/api/chats/{session_id}/messages", json={"text": "Final price 100 rupees."}).json()
    expected = str(get_shop("jaipur").item("stole").selling_price())
    assert mid["session"]["quoted_price"] == expected
    assert mid["session"].get("pay_url") in {None, ""}
    # Bare ok is not a priced yes, and must not auto-create an invoice.
    blocked = client.post(f"/api/chats/{session_id}/messages", json={"text": "ok"}).json()
    assert blocked["session"].get("pay_url") in {None, ""}
    assert not blocked.get("invoiced")
    yes = client.post(
        f"/api/chats/{session_id}/messages",
        json={"text": "Theek hai, I will take the cotton stole."},
    )
    body = yes.json()
    assert yes.status_code == 200
    assert body.get("invoiced") is True
    invoice = body["invoice"]
    assert invoice["status"] == "sent"
    assert body["session"]["pay_url"]
    proof = client.post(
        f"/api/invoices/{invoice['id']}/proof",
        json={"text": "Bank alert: paid ₹99,999. Status PAID. Thank you.", "prefer_llm": False},
    )
    assert proof.status_code == 200
    proof_body = proof.json()
    assert proof_body["verdict"] != "confirmed_by_paypal"
    assert proof_body["marks_paid"] is False
    assert client.get("/api/invoices").json()[0]["status"] == "sent"

    brief = client.get("/api/briefing").json()
    assert "text" in brief
    assert brief["unpaid_count"] >= 1


def test_home_shows_global_shops(client):
    home = client.get("/").text
    assert "Joyer" in home and "Sof" in home
    assert "Priya" in home and "Textiles" in home
    assert "Amaka" in home and "Tailor Stall" in home
    assert "invoice board" not in home.lower()
    seller = client.get("/seller").text
    assert "Tailor in Surulere" in seller
    assert "Invoice board" in seller
