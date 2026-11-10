"""Shared data shapes for extraction, checking, and invoices."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

from .money import format_ngn, format_usd, money, parse_amount


@dataclass
class LineItem:
    name: str
    quantity: Decimal
    unit_price_ngn: Decimal

    @property
    def line_total_ngn(self) -> Decimal:
        return money(self.quantity * self.unit_price_ngn)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "quantity": str(self.quantity),
            "unit_price_ngn": str(money(self.unit_price_ngn)),
            "line_total_ngn": str(self.line_total_ngn),
            "unit_price_ngn_display": format_ngn(self.unit_price_ngn),
            "line_total_ngn_display": format_ngn(self.line_total_ngn),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LineItem":
        qty = parse_amount(data.get("quantity"))
        price = parse_amount(data.get("unit_price_ngn"))
        if qty is None or price is None:
            raise ValueError("Each line item needs a quantity and a unit price in naira")
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_name": self.buyer_name,
            "buyer_email": self.buyer_email,
            "items": [item.to_dict() for item in self.items],
            "stated_total_ngn": None if self.stated_total_ngn is None else str(money(self.stated_total_ngn)),
            "stated_total_ngn_display": None if self.stated_total_ngn is None else format_ngn(self.stated_total_ngn),
            "notes": self.notes,
            "source": self.source,
            "raw_text": self.raw_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposedOrder":
        items = [LineItem.from_dict(item) for item in data.get("items") or []]
        return cls(
            buyer_name=str(data.get("buyer_name") or "").strip(),
            buyer_email=str(data.get("buyer_email") or "").strip(),
            items=items,
            stated_total_ngn=parse_amount(data.get("stated_total_ngn")),
            notes=str(data.get("notes") or ""),
            source=str(data.get("source") or "manual"),
            raw_text=str(data.get("raw_text") or ""),
        )


@dataclass
class ConvertedLine:
    name: str
    quantity: Decimal
    unit_price_ngn: Decimal
    unit_price_usd: Decimal
    line_total_ngn: Decimal
    line_total_usd: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "quantity": str(self.quantity),
            "unit_price_ngn": str(money(self.unit_price_ngn)),
            "unit_price_usd": str(money(self.unit_price_usd)),
            "line_total_ngn": str(money(self.line_total_ngn)),
            "line_total_usd": str(money(self.line_total_usd)),
            "unit_price_ngn_display": format_ngn(self.unit_price_ngn),
            "unit_price_usd_display": format_usd(self.unit_price_usd),
            "line_total_ngn_display": format_ngn(self.line_total_ngn),
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

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["computed_total_ngn"] = str(money(self.computed_total_ngn))
        data["computed_total_ngn_display"] = format_ngn(self.computed_total_ngn)
        data["usd_total"] = str(money(self.usd_total))
        data["usd_total_display"] = format_usd(self.usd_total)
        data["rate"] = str(self.rate)
        data["usd_items"] = [item.to_dict() for item in self.usd_items]
        return data


@dataclass
class PaypalInvoice:
    invoice_id: str
    status: str
    pay_url: str | None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "status": self.status,
            "pay_url": self.pay_url,
        }
