"""Demo seller shops. Three equal shops, not a Nigeria product with translations added on."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from .money import format_money, money


def parse_shop_time(value: str, timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    return datetime.fromisoformat(value).replace(tzinfo=tz)


def format_promo_end(ends_at: datetime, now: datetime | None = None) -> str:
    tz = ends_at.tzinfo or ZoneInfo("UTC")
    current = now or datetime.now(tz)
    if current.tzinfo is None:
        current = current.replace(tzinfo=tz)
    else:
        current = current.astimezone(tz)
    local = ends_at.astimezone(tz) if ends_at.tzinfo else ends_at.replace(tzinfo=tz)
    hour = local.strftime("%I").lstrip("0") or "12"
    stamp = f"{hour}:{local.strftime('%M %p')}"
    if local.date() == current.date():
        return f"today, {stamp}"
    return f"{local.strftime('%A')}, {local.day} {local.strftime('%B %Y')}, {stamp}"


@dataclass(frozen=True)
class CatalogItem:
    id: str
    name: str
    aliases: tuple[str, ...]
    list_price: Decimal
    promo_price: Decimal | None = None
    promo_ends_at: datetime | None = None

    def promo_is_active(self, now: datetime | None = None) -> bool:
        if self.promo_price is None or self.promo_ends_at is None:
            return False
        tz = self.promo_ends_at.tzinfo or ZoneInfo("UTC")
        current = now or datetime.now(tz)
        if current.tzinfo is None:
            current = current.replace(tzinfo=tz)
        else:
            current = current.astimezone(tz)
        return current <= self.promo_ends_at

    def selling_price(self, now: datetime | None = None) -> Decimal:
        if self.promo_is_active(now):
            return money(self.promo_price)
        return money(self.list_price)

    def allowed_prices(self, now: datetime | None = None) -> set[Decimal]:
        allowed = {money(self.list_price)}
        if self.promo_is_active(now):
            allowed.add(money(self.promo_price))
        return allowed

    def to_dict(self, currency: str, now: datetime | None = None) -> dict[str, Any]:
        selling = self.selling_price(now)
        active = self.promo_is_active(now)
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "list_price": str(money(self.list_price)),
            "list_price_display": format_money(self.list_price, currency),
            "selling_price": str(selling),
            "selling_price_display": format_money(selling, currency),
            "promo_active": active,
            "promo_price": str(money(self.promo_price)) if active else None,
            "promo_price_display": format_money(self.promo_price, currency) if active else None,
            "promo_ends_at": self.promo_ends_at.isoformat() if active and self.promo_ends_at else None,
            "promo_ends_display": format_promo_end(self.promo_ends_at, now) if active and self.promo_ends_at else None,
        }


@dataclass(frozen=True)
class Shop:
    id: str
    name: str
    city: str
    country: str
    language: str
    currency: str
    timezone: str
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

    def to_public(self, now: datetime | None = None) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "country": self.country,
            "language": self.language,
            "currency": self.currency,
            "timezone": self.timezone,
            "seller_name": self.seller_name,
            "seller_title": self.seller_title,
            "tone": self.tone,
            "greeting": self.greeting,
            "items": [item.to_dict(self.currency, now) for item in self.items],
        }


LAGOS_TZ = "Africa/Lagos"
MEXICO_TZ = "America/Mexico_City"
JAIPUR_TZ = "Asia/Kolkata"

# Live promo windows are stored with a real end time. Judges seeing the demo
# before Thursday, 12 November 2026, 9:00 PM in the shop's local time get the
# promo; after that the agent states the list price and never revives the deal.
PROMO_END_LAGOS = parse_shop_time("2026-11-12T21:00:00", LAGOS_TZ)
PROMO_END_MEXICO = parse_shop_time("2026-11-12T21:00:00", MEXICO_TZ)
PROMO_END_JAIPUR = parse_shop_time("2026-11-12T21:00:00", JAIPUR_TZ)
# A real expired promo, kept on the catalog so expiry can be tested honestly.
EXPIRED_GELE_PROMO_END = parse_shop_time("2026-11-09T21:00:00", LAGOS_TZ)


SHOPS: dict[str, Shop] = {
    "lagos": Shop(
        id="lagos",
        name="Amaka's Tailor Stall",
        city="Lagos",
        country="Nigeria",
        language="pcm",
        currency="NGN",
        timezone=LAGOS_TZ,
        seller_name="Amaka",
        seller_title="tailor",
        tone="Warm, funny Lagos trader English mixed with Nigerian Pidgin. Short sentences. Never rude.",
        greeting="You are welcome o. I get native shirts, Ankara, and gele. Wetin you wan buy?",
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "native-shirt",
                "native shirt",
                ("native shirts", "shirt", "native"),
                Decimal("25000"),
                promo_price=Decimal("22000"),
                promo_ends_at=PROMO_END_LAGOS,
            ),
            CatalogItem("ankara", "Ankara", ("ankara fabric", "ankara yard", "fabric"), Decimal("8000")),
            CatalogItem(
                "gele",
                "gele",
                ("headwrap", "head wrap"),
                Decimal("12000"),
                promo_price=Decimal("9500"),
                promo_ends_at=EXPIRED_GELE_PROMO_END,
            ),
        ),
    ),
    "mexico": Shop(
        id="mexico",
        name="Joyería Sofía",
        city="Mexico City",
        country="Mexico",
        language="es",
        currency="MXN",
        timezone=MEXICO_TZ,
        seller_name="Sofía",
        seller_title="jeweler",
        tone="Friendly Mexican Spanish, polite and warm, like a stall holder in a city market. Short sentences.",
        greeting="Hola, bienvenida. Tengo aretes de aro de plata y un brazalete de cuero. ¿Qué te gusta?",
        default_buyer_name="Comprador de prueba",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "earrings",
                "aretes de aro de plata",
                ("aretes", "aros", "earrings", "silver hoops", "hoops", "plata"),
                Decimal("850"),
                promo_price=Decimal("760"),
                promo_ends_at=PROMO_END_MEXICO,
            ),
            CatalogItem(
                "cuff",
                "brazalete de cuero",
                ("brazalete", "cuff", "leather cuff", "pulsera", "cuero"),
                Decimal("1200"),
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
        timezone=JAIPUR_TZ,
        seller_name="Priya",
        seller_title="textile seller",
        tone="Polite Hindi and Hinglish, warm and patient, like a shopkeeper in a Jaipur bazaar. Short sentences.",
        greeting="Namaste, welcome. Mere paas block-print scarf aur cotton stole hai. Aapko kya dekhna hai?",
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "scarf",
                "block-print scarf",
                ("scarf", "dupatta", "block print", "block-print", "print scarf"),
                Decimal("1800"),
                promo_price=Decimal("1550"),
                promo_ends_at=PROMO_END_JAIPUR,
            ),
            CatalogItem(
                "stole",
                "cotton stole",
                ("stole", "cotton", "shawl"),
                Decimal("950"),
            ),
        ),
    ),
}


def list_shops() -> list[Shop]:
    return [SHOPS[key] for key in ("lagos", "mexico", "jaipur")]


def get_shop(shop_id: str) -> Shop | None:
    return SHOPS.get((shop_id or "").strip().lower())
