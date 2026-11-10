from decimal import Decimal

from stallpay.checker import check_order
from stallpay.models import LineItem, ProposedOrder
from stallpay.paypal.mock import MockPaypalClient, reset_store


def _ready_order():
    return ProposedOrder(
        buyer_name="Tunde Okoro",
        buyer_email="tunde.okoro@example.com",
        items=[LineItem(name="native shirts", quantity=Decimal("2"), unit_price_ngn=Decimal("25000"))],
        stated_total_ngn=Decimal("50000"),
    )


def test_mock_create_send_get_remind_and_pay():
    reset_store()
    client = MockPaypalClient("http://testserver")
    order = _ready_order()
    check = check_order(order)
    created = client.create_invoice(order, check, "note")
    assert created.status == "DRAFT"
    sent = client.send_invoice(created.invoice_id)
    assert sent.status == "SENT"
    assert sent.pay_url.endswith(created.invoice_id)
    reminded = client.remind(created.invoice_id)
    assert reminded.raw["reminded"] is True
    paid = client.mark_paid(created.invoice_id)
    assert paid.status == "PAID"
    assert client.get_invoice(created.invoice_id).status == "PAID"


def test_cannot_remind_a_paid_mock_invoice():
    reset_store()
    client = MockPaypalClient("http://testserver")
    order = _ready_order()
    created = client.create_invoice(order, check_order(order), "note")
    client.send_invoice(created.invoice_id)
    client.mark_paid(created.invoice_id)
    try:
        client.remind(created.invoice_id)
        assert False, "should have failed"
    except ValueError:
        pass
