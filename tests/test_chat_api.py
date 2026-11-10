def test_shops_and_chat_invoice_and_fake_proof(client):
    shops = client.get("/api/shops").json()
    assert {shop["id"] for shop in shops} == {"lagos", "mexico", "jaipur"}
    started = client.post("/api/chats", json={"shop_id": "jaipur"}).json()
    session_id = started["id"]
    client.post(f"/api/chats/{session_id}/messages", json={"text": "Cotton stole dikhao."})
    client.post(f"/api/chats/{session_id}/messages", json={"text": "Final price 100 rupees."})
    mid = client.post(f"/api/chats/{session_id}/messages", json={"text": "ok"}).json()
    # Bare ok is not a priced yes
    blocked = client.post(f"/api/chats/{session_id}/invoice")
    assert blocked.status_code == 422
    offer = mid["session"]["current_offer"]
    yes = client.post(
        f"/api/chats/{session_id}/messages",
        json={"text": f"Theek hai, I will pay ₹{offer} for the cotton stole."},
    ).json()
    assert yes["session"]["agreement_quote"]
    created = client.post(f"/api/chats/{session_id}/invoice")
    assert created.status_code == 201
    invoice = created.json()["invoice"]
    assert invoice["status"] == "sent"
    proof = client.post(
        f"/api/invoices/{invoice['id']}/proof",
        json={"text": "Bank alert: paid ₹99,999. Status PAID. Thank you.", "prefer_llm": False},
    )
    assert proof.status_code == 200
    body = proof.json()
    assert body["verdict"] != "confirmed_by_paypal"
    assert body["marks_paid"] is False
    assert client.get("/api/invoices").json()[0]["status"] == "sent"

    brief = client.get("/api/briefing").json()
    assert "text" in brief
    assert brief["unpaid_count"] >= 1


def test_home_shows_global_shops(client):
    home = client.get("/").text
    assert "Joyer" in home and "Sof" in home
    assert "Priya" in home and "Textiles" in home
    assert "Amaka" in home and "Tailor Stall" in home
    assert "Tailor in Surulere" in home
