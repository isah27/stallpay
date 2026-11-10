"""Demo seller shops. Three equal shops in different cities, English by default."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from .languages import normalize_language
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

    def search_names(self) -> tuple[str, ...]:
        bare = re.sub(r"\s*\([^)]*\)\s*", " ", self.name).strip()
        names = [self.name, bare, self.id, *self.aliases]
        seen: list[str] = []
        for name in names:
            cleaned = (name or "").strip()
            if cleaned and cleaned.lower() not in {item.lower() for item in seen}:
                seen.append(cleaned)
        return tuple(seen)

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
    greetings: dict[str, str]
    default_buyer_name: str
    default_buyer_email: str
    items: tuple[CatalogItem, ...]

    def item(self, item_id: str) -> CatalogItem | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def greeting_for(self, language: str | None = None) -> str:
        lang = normalize_language(language, default="en")
        return self.greetings.get(lang) or self.greetings.get("en") or self.greeting

    def find_items(self, text: str) -> list[CatalogItem]:
        lowered = (text or "").lower()
        found: list[CatalogItem] = []
        for item in self.items:
            names = item.search_names()
            if any(alias.lower() in lowered for alias in names if alias):
                found.append(item)
        if found:
            return found
        ordinal = parse_item_ordinal(text, len(self.items))
        if ordinal is not None:
            return [self.items[ordinal]]
        return []

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


_ORDINAL_PATTERNS = (
    (0, re.compile(
        r"\b((the|el|la|le)\s+)?(first|1st|primer[oa]|premier|premi[eè]re|pehla|pehle)\b|"
        r"\b(item|number|no\.?|n[uú]mero|#)\s*1\b|"
        r"[\u0900-\u097F]*पहला",
        re.IGNORECASE,
    )),
    (1, re.compile(
        r"\b((the|el|la|le)\s+)?(second|2nd|segund[oa]|deuxi[eè]me|doosr[aei])\b|"
        r"\b(item|number|no\.?|n[uú]mero|#)\s*2\b|"
        r"[\u0900-\u097F]*दूसरा",
        re.IGNORECASE,
    )),
    (2, re.compile(
        r"\b((the|el|la|le)\s+)?(third|3rd|tercer[oa]|troisi[eè]me|teesr[aei])\b|"
        r"\b(item|number|no\.?|n[uú]mero|#)\s*3\b|"
        r"[\u0900-\u097F]*तीसरा",
        re.IGNORECASE,
    )),
)
_BARE_INDEX_RE = re.compile(r"^\s*#?\s*([1-9])\s*$")


def parse_item_ordinal(text: str, catalog_size: int) -> int | None:
    raw = (text or "").strip()
    if not raw or catalog_size <= 0:
        return None
    bare = _BARE_INDEX_RE.match(raw)
    if bare:
        index = int(bare.group(1)) - 1
        return index if index < catalog_size else None
    for index, pattern in _ORDINAL_PATTERNS:
        if index < catalog_size and pattern.search(raw):
            return index
    return None


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


LAGOS_GREETINGS = {
    "en": "Welcome. I have native shirts, Ankara, and gele (headwraps). What would you like to buy?",
    "es": "Bienvenido. Tengo camisas nativas, Ankara y gele. ¿Qué te gustaría comprar?",
    "hi": "Namaste, welcome. Mere paas native shirts, Ankara aur gele hain. Aapko kya chahiye?",
    "pcm": "You are welcome o. I get native shirts, Ankara, and gele. Wetin you wan buy?",
    "fr": "Bienvenue. J'ai des chemises traditionnelles, de l'Ankara et des gele. Que souhaitez-vous acheter ?",
}
MEXICO_GREETINGS = {
    "en": "Welcome. I have silver hoop earrings (aretes) and a leather cuff (brazalete). What would you like to buy?",
    "es": "Hola, bienvenida. Tengo aretes de aro de plata y un brazalete de cuero. ¿Qué te gusta?",
    "hi": "Namaste, welcome. Mere paas silver hoop earrings aur leather cuff hain. Aapko kya dekhna hai?",
    "pcm": "You are welcome. I get silver hoop earrings and a leather cuff. Wetin you wan buy?",
    "fr": "Bienvenue. J'ai des créoles en argent (aretes) et un bracelet en cuir (brazalete). Que souhaitez-vous acheter ?",
}
JAIPUR_GREETINGS = {
    "en": "Welcome. I have a block-print scarf (dupatta) and a cotton stole. What would you like to buy?",
    "es": "Bienvenido. Tengo un pañuelo block-print (dupatta) y una estola de algodón. ¿Qué te gustaría ver?",
    "hi": "Namaste, welcome. Mere paas block-print scarf aur cotton stole hai. Aapko kya dekhna hai?",
    "pcm": "You are welcome. I get block-print scarf and cotton stole. Wetin you wan buy?",
    "fr": "Bienvenue. J'ai une écharpe block-print (dupatta) et une étole en coton. Que souhaitez-vous acheter ?",
}


SHOPS: dict[str, Shop] = {
    "lagos": Shop(
        id="lagos",
        name="Amaka's Tailor Stall",
        city="Lagos",
        country="Nigeria",
        language="en",
        currency="NGN",
        timezone=LAGOS_TZ,
        seller_name="Amaka",
        seller_title="tailor",
        tone="Warm, funny Lagos trader English, with Pidgin if the buyer chose Pidgin. Short sentences. Never rude.",
        greeting=LAGOS_GREETINGS["en"],
        greetings=LAGOS_GREETINGS,
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "native-shirt",
                "native shirt",
                ("native shirts", "shirt", "native", "camisa nativa", "chemise"),
                Decimal("25000"),
                promo_price=Decimal("22000"),
                promo_ends_at=PROMO_END_LAGOS,
            ),
            CatalogItem("ankara", "Ankara", ("ankara fabric", "ankara yard", "fabric"), Decimal("8000")),
            CatalogItem(
                "gele",
                "gele (headwrap)",
                ("gele", "headwrap", "head wrap", "headwraps"),
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
        language="en",
        currency="MXN",
        timezone=MEXICO_TZ,
        seller_name="Sofía",
        seller_title="jeweler",
        tone="Friendly and warm, like a stall holder in a Mexico City market. Short sentences. Reply in the language the buyer selected.",
        greeting=MEXICO_GREETINGS["en"],
        greetings=MEXICO_GREETINGS,
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "earrings",
                "silver hoop earrings (aretes)",
                (
                    "aretes de aro de plata",
                    "aretes de aro",
                    "aretes",
                    "aros",
                    "earrings",
                    "silver hoop earrings",
                    "silver hoops",
                    "hoops",
                    "plata",
                    "creoles",
                    "créoles",
                    "boucles d'oreille",
                    "boucles d'oreilles",
                ),
                Decimal("850"),
                promo_price=Decimal("760"),
                promo_ends_at=PROMO_END_MEXICO,
            ),
            CatalogItem(
                "cuff",
                "leather cuff (brazalete)",
                (
                    "brazalete de cuero",
                    "brazalete",
                    "cuff",
                    "leather cuff",
                    "pulsera",
                    "cuero",
                    "bracelet",
                    "bracelet en cuir",
                ),
                Decimal("1200"),
            ),
        ),
    ),
    "jaipur": Shop(
        id="jaipur",
        name="Priya's Textiles",
        city="Jaipur",
        country="India",
        language="en",
        currency="INR",
        timezone=JAIPUR_TZ,
        seller_name="Priya",
        seller_title="textile seller",
        tone="Polite and warm, like a shopkeeper in a Jaipur bazaar. Short sentences. Reply in the language the buyer selected.",
        greeting=JAIPUR_GREETINGS["en"],
        greetings=JAIPUR_GREETINGS,
        default_buyer_name="Sandbox Buyer",
        default_buyer_email="buyer@stallpay.example",
        items=(
            CatalogItem(
                "scarf",
                "block-print scarf (dupatta)",
                (
                    "block-print scarf",
                    "block print scarf",
                    "scarf",
                    "dupatta",
                    "block print",
                    "block-print",
                    "print scarf",
                    "pañuelo",
                    "echarpe",
                    "écharpe",
                ),
                Decimal("1800"),
                promo_price=Decimal("1550"),
                promo_ends_at=PROMO_END_JAIPUR,
            ),
            CatalogItem(
                "stole",
                "cotton stole",
                ("stole", "cotton stole", "cotton", "shawl", "estola", "étole", "etole"),
                Decimal("950"),
            ),
        ),
    ),
}


def list_shops() -> list[Shop]:
    return [SHOPS[key] for key in ("lagos", "mexico", "jaipur")]


def get_shop(shop_id: str) -> Shop | None:
    return SHOPS.get((shop_id or "").strip().lower())
