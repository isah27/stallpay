from stallpay.webhooks import handle_webhook_event, invoice_id_from_event, map_paypal_status


def test_map_paypal_status():
    assert map_paypal_status("PAID") == "paid"
    assert map_paypal_status("UNPAID") == "sent"
    assert map_paypal_status("CANCELLED") == "cancelled"
    assert map_paypal_status("DRAFT") == "draft"


def test_invoice_id_from_nested_event():
    event = {"event_type": "INVOICING.INVOICE.PAID", "resource": {"invoice": {"id": "INV2-ABC"}}}
    assert invoice_id_from_event(event) == "INV2-ABC"


def test_handle_unknown_invoice_is_not_ok(client):
    result = handle_webhook_event(
        {"event_type": "INVOICING.INVOICE.PAID", "resource": {"id": "MOCK-MISSING"}}
    )
    assert result["ok"] is False
