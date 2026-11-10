"""Shared data shapes for extraction, checking, and invoices."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

from .money import format_money, format_ngn, format_usd, money, parse_amount


def _price_from(data: dict[str, Any], *keys: str) -> Decimal | None:
    for key in keys:
        if key in data and data[key] is not None and data[key] != "":
            return parse_amount(data[key])
    return None


@dataclass
class LineItem:
    name: str
    quantity: Decimal
    unit_price_ngn: Decimal

    @property
    def unit_price(self) -> Decimal:
        return self.unit_price_ngn

    @property
    def line_total_ngn(self) -> Decimal:
        return money(self.quantity * self.unit_price_ngn)

    @property
    def line_total(self) -> Decimal:
        return self.line_total_ngn

    def to_dict(self, currency: str = "NGN") -> dict[str, Any]:
        return {
            "name": self.name,
            "quantity": str(self.quantity),
            "unit_price_ngn": str(money(self.unit_price_ngn)),
            "unit_price": str(money(self.unit_price_ngn)),
            "line_total_ngn": str(self.line_total_ngn),
            "line_total": str(self.line_total),
            "currency": currency,
            "unit_price_ngn_display": format_money(self.unit_price_ngn, currency),
            "unit_price_display": format_money(self.unit_price_ngn, currency),
            "line_total_ngn_display": format_money(self.line_total_ngn, currency),
            "line_total_display": format_money(self.line_total, currency),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LineItem":
        qty = parse_amount(data.get("quantity"))
        price = _price_from(data, "unit_price_ngn", "unit_price")
        if qty is None or price is None:
            raise ValueError("Each line item needs a quantity and a unit price")
        name = str(data.get("name") or "").strip()
        if not name:
            raise ValueError("Each line item needs a name")
        return cls(name=name, quantity=qty, unit_price_ngn=price)


@dataclass
class ProposedOrder:
    buyer_name: str
    buyer_email: str
    items: list[LineItem]
    stated_total_ngn: Decimal | None
    notes: str = ""
    source: str = "heuristic"
    raw_text: str = ""
    currency: str = "NGN"
    agreement_quote: str = ""
    agreement_speaker: str = ""

    @property
    def stated_total(self) -> Decimal | None:
        return self.stated_total_ngn

    def to_dict(self) -> dict[str, Any]:
        currency = (self.currency or "NGN").upper()
        stated = None if self.stated_total_ngn is None else str(money(self.stated_total_ngn))
        stated_display = None if self.stated_total_ngn is None else format_money(self.stated_total_ngn, currency)
        return {
            "buyer_name": self.buyer_name,
            "buyer_email": self.buyer_email,
            "items": [item.to_dict(currency) for item in self.items],
            "stated_total_ngn": stated,
            "stated_total": stated,
            "stated_total_ngn_display": stated_display,
            "stated_total_display": stated_display,
            "currency": currency,
            "notes": self.notes,
            "source": self.source,
            "raw_text": self.raw_text,
            "agreement_quote": self.agreement_quote,
            "agreement_speaker": self.agreement_speaker,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposedOrder":
        items = [LineItem.from_dict(item) for item in data.get("items") or []]
        stated = _price_from(data, "stated_total_ngn", "stated_total")
        return cls(
            buyer_name=str(data.get("buyer_name") or "").strip(),
            buyer_email=str(data.get("buyer_email") or "").strip(),
            items=items,
            stated_total_ngn=stated,
            notes=str(data.get("notes") or ""),
            source=str(data.get("source") or "manual"),
            raw_text=str(data.get("raw_text") or ""),
            currency=str(data.get("currency") or "NGN").upper(),
            agreement_quote=str(data.get("agreement_quote") or ""),
            agreement_speaker=str(data.get("agreement_speaker") or ""),
        )


@dataclass
class ConvertedLine:
    name: str
    quantity: Decimal
    unit_price_ngn: Decimal
    unit_price_usd: Decimal
    line_total_ngn: Decimal
    line_total_usd: Decimal
    currency: str = "NGN"

    def to_dict(self) -> dict[str, Any]:
        currency = (self.currency or "NGN").upper()
        return {
            "name": self.name,
            "quantity": str(self.quantity),
            "currency": currency,
            "unit_price_ngn": str(money(self.unit_price_ngn)),
            "unit_price": str(money(self.unit_price_ngn)),
            "unit_price_usd": str(money(self.unit_price_usd)),
            "line_total_ngn": str(money(self.line_total_ngn)),
            "line_total": str(money(self.line_total_ngn)),
            "line_total_usd": str(money(self.line_total_usd)),
            "unit_price_ngn_display": format_money(self.unit_price_ngn, currency),
            "unit_price_display": format_money(self.unit_price_ngn, currency),
            "unit_price_usd_display": format_usd(self.unit_price_usd),
            "line_total_ngn_display": format_money(self.line_total_ngn, currency),
            "line_total_display": format_money(self.line_total_ngn, currency),
            "line_total_usd_display": format_usd(self.line_total_usd),
        }


@dataclass
class CheckResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    computed_total_ngn: Decimal = Decimal("0.00")
    usd_total: Decimal = Decimal("0.00")
    usd_items: list[ConvertedLine] = field(default_factory=list)
    rate: Decimal = Decimal("0")
    rate_as_of: str = ""
    currency: str = "NGN"
    floor_total: Decimal | None = None
    floor_held: bool = True
    agreement_quote: str = ""

    @property
    def computed_total(self) -> Decimal:
        return self.computed_total_ngn

    def to_dict(self) -> dict[str, Any]:
        currency = (self.currency or "NGN").upper()
        data = asdict(self)
        data["computed_total_ngn"] = str(money(self.computed_total_ngn))
        data["computed_total"] = str(money(self.computed_total_ngn))
        data["computed_total_ngn_display"] = format_money(self.computed_total_ngn, currency)
        data["computed_total_display"] = format_money(self.computed_total_ngn, currency)
        data["usd_total"] = str(money(self.usd_total))
        data["usd_total_display"] = format_usd(self.usd_total)
        data["rate"] = str(self.rate)
        data["currency"] = currency
        data["floor_total"] = None if self.floor_total is None else str(money(self.floor_total))
        data["floor_total_display"] = None if self.floor_total is None else format_money(self.floor_total, currency)
        data["usd_items"] = [item.to_dict() for item in self.usd_items]
        return data


@dataclass
class PaypalInvoice:
    invoice_id: str
    status: str
    pay_url: str | None
    raw: dict[str, Any] = field(default_factory=dict)
    amount_usd: str | None = None
    invoice_number: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "status": self.status,
            "pay_url": self.pay_url,
            "amount_usd": self.amount_usd,
            "invoice_number": self.invoice_number,
        }
