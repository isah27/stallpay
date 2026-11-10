from stallpay.samples import get_sample


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["paypal_mode"] == "mock"


def test_home_and_metrics_pages(client):
    home = client.get("/")
    assert home.status_code == 200
    assert "StallPay" in home.text
    assert "Joyería Sofía" in home.text or "Joyer" in home.text
    assert "Seller tools" in home.text
    assert "Tailor in Surulere" not in home.text
    seller = client.get("/seller")
    assert seller.status_code == 200
    assert "Tailor in Surulere" in seller.text
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "5" in metrics.text
    data = client.get("/metrics?format=json").json()
    assert data["success_extracted_and_checked"] == 5
    assert data["failure_blocked_by_checker"] == 3
    assert data["price_integrity"]["held"] == data["price_integrity"]["total"]
    assert data["promo_expiry"]["held"] == data["promo_expiry"]["total"]
    assert data["agreement_gate"]["false_invoice_count"] == 0


def test_preview_sample_and_create_invoice_end_to_end(client):
    sample = get_sample("tailor")
    preview = client.post("/api/preview", json={"text": sample["text"], "prefer_llm": False})
    assert preview.status_code == 200
    body = preview.json()
    assert body["check"]["ok"] is True
    created = client.post("/api/invoices", json={"order": body["order"], "raw_text": sample["text"]})
    assert created.status_code == 201
    invoice = created.json()["invoice"]
    assert invoice["status"] == "sent"
    assert invoice["pay_url"].startswith("http://testserver/mock-pay/")

    pay = client.get(invoice["pay_url"].replace("http://testserver", ""))
    assert pay.status_code == 200
    paid = client.post(invoice["pay_url"].replace("http://testserver", ""))
    assert paid.status_code == 200
    assert paid.json()["invoice"]["status"] == "PAID"

    board = client.get("/api/invoices").json()
    assert board[0]["status"] == "paid"

    refresh = client.post(f"/api/invoices/{invoice['id']}/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["status"] == "paid"


def test_checker_blocks_create_for_bad_total(client):
    sample = get_sample("total_mismatch")
    res = client.post("/api/invoices", json={"text": sample["text"]})
    assert res.status_code == 422
    body = res.json()
    assert body["blocked"] is True
    assert client.get("/api/invoices").json() == []


def test_remind_unpaid_invoice(client):
    sample = get_sample("food")
    preview = client.post("/api/preview", json={"text": sample["text"]}).json()
    created = client.post("/api/invoices", json={"order": preview["order"]}).json()["invoice"]
    reminded = client.post(f"/api/invoices/{created['id']}/remind")
    assert reminded.status_code == 200
    assert reminded.json()["reminder_sent"] is True


def test_webhook_marks_paid(client):
    sample = get_sample("pidgin")
    preview = client.post("/api/preview", json={"text": sample["text"]}).json()
    created = client.post("/api/invoices", json={"order": preview["order"]}).json()["invoice"]
    event = {
        "event_source": "stallpay-mock",
        "event_type": "INVOICING.INVOICE.PAID",
        "resource": {"id": created["paypal_invoice_id"], "status": "PAID"},
    }
    res = client.post("/webhooks/paypal", json=event)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert client.get("/api/invoices").json()[0]["status"] == "paid"


def test_edit_before_send_recheck(client):
    sample = get_sample("accessories")
    preview = client.post("/api/preview", json={"text": sample["text"]}).json()
    order = preview["order"]
    original_total = order["stated_total_ngn"]
    order["stated_total_ngn"] = "1.00"
    blocked = client.post("/api/preview", json={"order": order})
    assert blocked.json()["blocked"] is True
    order["stated_total_ngn"] = original_total
    ok = client.post("/api/preview", json={"order": order})
    assert ok.json()["blocked"] is False


def test_buyer_page_is_customer_facing(client):
    home = client.get("/").text
    assert "Select the shop you want to buy from." in home
    assert "StallPay" in home
    assert "Seller tools" in home
    for forbidden in (
        "Step 1",
        "Step 2",
        "1. Shop",
        "2. Item",
        "Mode:",
        "1 USD",
        "Published numbers",
        "Model drafts",
        "Scripted agent",
        "class=\"steps\"",
        "metrics-strip",
        "invoice board",
        "usage-note",
        "PayPal sandbox",
        "price conversion",
    ):
        assert forbidden not in home
    # Conversion rates and mode stay on seller tools, not the buyer page.
    seller = client.get("/seller").text
    assert "Mode:" in seller
    assert "Invoice board" in seller
