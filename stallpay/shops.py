"""Demo seller shops. Three equal shops, not a Nigeria product with translations added on."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

from .money import format_money, money


@dataclass(frozen=True)
class CatalogItem:
    id: str
    name: str
    aliases: tuple[str, ...]
    list_price: Decimal
    floor_price: Decimal

    def to_dict(self, currency: str) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "list_price": str(money(self.list_price)),
            "floor_price": str(money(self.floor_price)),
            "list_price_display": format_money(self.list_price, currency),
            "floor_price_display": format_money(self.floor_price, currency),
        }


@dataclass(frozen=True)
class Shop:
    id: str
    name: str
    city: str
    country: str
    language: str
    currency: str
    seller_name: str
    seller_title: str
    tone: str
    greeting: str
    default_buyer_name: str
    default_buyer_email: str
    items: tuple[CatalogItem, ...]

    def item(self, item_id: str) -> CatalogItem | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def find_items(self, text: str) -> list[CatalogItem]:
        lowered = (text or "").lower()
        found: list[CatalogItem] = []
        for item in self.items:
            names = (item.name, item.id, *item.aliases)
            if any(alias.lower() in lowered for alias in names if alias):
                found.append(item)
        return found

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "language": self.language,
            "currency": self.currency,
            "seller_name": self.seller_name,
            "seller_title": self.seller_title,
            "tone": self.tone,
            "greeting": self.greeting,
            "items": [item.to_dict(self.currency) for item in self.items],
        }


SHOPS: dict[str, Shop] = {
    "lagos": Shop(
        id="lagos",
        name="Amaka's Tailor Stall",
        city="Lagos",
        country="Nigeria",
        language="pcm",
        currency="NGN",
        seller_name="Amaka",
        seller_title="tailor",
        tone="Warm, funny Lagos trader English mixed with Nigerian Pidgin. Short sentences. Never rude.",
        greeting=(
            "You are welcome o. I get native shirts at ₦25,000, Ankara at ₦8,000 a yard, "
            "and gele at ₦12,000. Wetin you wan buy?"
        ),
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem("native-shirt", "native shirt", ("native shirts", "shirt", "native"), Decimal("25000"), Decimal("22000")),
            CatalogItem("ankara", "Ankara", ("ankara fabric", "ankara yard", "fabric"), Decimal("8000"), Decimal("6500")),
            CatalogItem("gele", "gele", ("headwrap", "head wrap"), Decimal("12000"), Decimal("10000")),
        ),
    ),
    "mexico": Shop(
        id="mexico",
        name="Joyería Sofía",
        city="Mexico City",
        country="Mexico",
        language="es",
        currency="MXN",
        seller_name="Sofía",
        seller_title="jeweler",
        tone="Friendly Mexican Spanish, polite and warm, like a stall holder in a city market. Short sentences.",
        greeting=(
            "Hola, bienvenida. Tengo aretes de aro de plata a MX$850 y un brazalete de cuero a MX$1,200. "
            "¿Qué te gusta?"
        ),
        default_buyer_name="Comprador de prueba",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "earrings",
                "aretes de aro de plata",
                ("aretes", "aros", "earrings", "silver hoops", "hoops", "plata"),
                Decimal("850"),
                Decimal("720"),
            ),
            CatalogItem(
                "cuff",
                "brazalete de cuero",
                ("brazalete", "cuff", "leather cuff", "pulsera", "cuero"),
                Decimal("1200"),
                Decimal("980"),
            ),
        ),
    ),
    "jaipur": Shop(
        id="jaipur",
        name="Priya's Textiles",
        city="Jaipur",
        country="India",
        language="hi",
        currency="INR",
        seller_name="Priya",
        seller_title="textile seller",
        tone="Polite Hindi and Hinglish, warm and patient, like a shopkeeper in a Jaipur bazaar. Short sentences.",
        greeting=(
            "Namaste, welcome. Block-print scarf ₹1,800 hai, cotton stole ₹950. "
            "Aapko kya dekhna hai?"
        ),
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "scarf",
                "block-print scarf",
                ("scarf", "dupatta", "block print", "block-print", "print scarf"),
                Decimal("1800"),
                Decimal("1500"),
            ),
            CatalogItem(
                "stole",
                "cotton stole",
                ("stole", "cotton", "shawl"),
                Decimal("950"),
                Decimal("800"),
            ),
        ),
    ),
}


def list_shops() -> list[Shop]:
    return [SHOPS[key] for key in ("lagos", "mexico", "jaipur")]


def get_shop(shop_id: str) -> Shop | None:
    return SHOPS.get((shop_id or "").strip().lower())
