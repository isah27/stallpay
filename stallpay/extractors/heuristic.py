"""Regex/heuristic extractor that works offline on the canned demo chats."""
from __future__ import annotations

import re
from decimal import Decimal

from ..models import LineItem, ProposedOrder
from ..money import money, parse_amount

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
NAME_IS_RE = re.compile(r"\bname is\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)+)", re.IGNORECASE)
EMDASH_NAME_RE = re.compile(r"[—–-]\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)+)\s*$")
TOTAL_RE = re.compile(
    r"\b(?:total(?:\s+na)?|that's|thats|that is)\s*(?:na\s*)?(?:is\s*)?₦?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
QTY_AT_PRICE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s+([A-Za-z][A-Za-z0-9][A-Za-z0-9 '&/\-]*?)\s+(?:at|@)\s*₦?\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
NAME_IS_PRICE_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9][A-Za-z0-9 '&/\-]*?)\s+(?:is|na)\s*₦\s*([\d,]+(?:\.\d{1,2})?)"
    r"(?:\s+(?:each|per\s+([A-Za-z]+)))?",
    re.IGNORECASE,
)
BARE_PRICE_RE = re.compile(
    r"\b(each\s+)?([A-Za-z][A-Za-z0-9][A-Za-z0-9 '&/\-]*?)\s*₦\s*([\d,]+(?:\.\d{1,2})?)"
    r"(?:\s+(?:each|per\s+([A-Za-z]+)))?",
    re.IGNORECASE,
)
QTY_PHRASE_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s+(?:packs?\s+of\s+|yards?\s+of\s+)?([A-Za-z][A-Za-z0-9'/-]*(?:\s+[A-Za-z][A-Za-z0-9'/-]*){0,4})",
    re.IGNORECASE,
)
QTY_UNIT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s+(yards?|packs?|pcs|pieces)\b", re.IGNORECASE)

STOP_QTY_TAILS = {
    "each", "total", "and", "for", "ready", "please", "invoice", "me", "at",
    "how", "much", "the", "my", "sister", "wedding", "pack", "packs", "yard",
    "yards", "is", "na", "want", "need", "wan",
}


def _clean_name(name: str) -> str:
    name = re.split(r"\s+(?:and|for|at|@)\s+", name, maxsplit=1, flags=re.IGNORECASE)[0]
    name = re.sub(r"\s+", " ", name).strip(" .,;:")
    name = re.sub(
        r"\b(for my sister wedding|ready|please|invoice)\b",
        "",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"\s+", " ", name).strip(" .,;:")
    name = re.sub(r"\b(each|per pack|per yard|per piece)\b", "", name, flags=re.IGNORECASE).strip()
    if name.lower().startswith("each "):
        name = name[5:].strip()
    return name


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _names_match(a: str, b: str) -> bool:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    if na.rstrip("s") == nb.rstrip("s") and min(len(na), len(nb)) > 3:
        return True
    return False


def _extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def _extract_name(text: str, email: str) -> str:
    match = NAME_IS_RE.search(text)
    if match:
        return match.group(1).strip()
    for line in text.splitlines():
        if "invoice to" in line.lower() and "—" in line:
            after = line.split("—", 1)[-1].strip()
            if after and "@" not in after:
                return after
        em = EMDASH_NAME_RE.search(line.strip())
        if em and "@" not in em.group(1):
            return em.group(1).strip()
    return ""


def _extract_total(text: str) -> Decimal | None:
    matches = list(TOTAL_RE.finditer(text))
    if not matches:
        return None
    return parse_amount(matches[-1].group(1))


def _qty_mentions(text: str) -> list[tuple[Decimal, str, tuple[int, int]]]:
    found: list[tuple[Decimal, str, tuple[int, int]]] = []
    for match in QTY_PHRASE_RE.finditer(text):
        qty = parse_amount(match.group(1))
        name = _clean_name(match.group(2))
        low = name.lower()
        if qty is None or qty <= 0:
            continue
        if low in STOP_QTY_TAILS:
            continue
        if "ready" in low or "how much" in low:
            continue
        found.append((qty, name, match.span()))
    return found


def _price_entries(text: str) -> list[dict]:
    entries: list[dict] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(start < b and end > a for a, b in occupied)

    for match in QTY_AT_PRICE_RE.finditer(text):
        qty = parse_amount(match.group(1))
        price = parse_amount(match.group(3))
        name = _clean_name(match.group(2))
        if qty is None or price is None or not name:
            continue
        entries.append(
            {"name": name, "quantity": qty, "unit_price_ngn": price, "span": match.span()}
        )
        occupied.append(match.span())

    for match in NAME_IS_PRICE_RE.finditer(text):
        if overlaps(*match.span()):
            continue
        name = _clean_name(match.group(1))
        if name.lower() in {"total", "that's", "thats", "that"} or name.lower().startswith("total "):
            continue
        price = parse_amount(match.group(2))
        if price is None or not name:
            continue
        entries.append(
            {"name": name, "quantity": None, "unit_price_ngn": price, "span": match.span()}
        )
        occupied.append(match.span())

    for match in BARE_PRICE_RE.finditer(text):
        if overlaps(*match.span()):
            continue
        name = _clean_name((match.group(1) or "") + (match.group(2) or ""))
        if name.lower() in {"total", "that's", "thats", "that"} or name.lower().startswith("total "):
            continue
        price = parse_amount(match.group(3))
        if price is None or not name:
            continue
        entries.append(
            {"name": name, "quantity": None, "unit_price_ngn": price, "span": match.span()}
        )
        occupied.append(match.span())
    return entries


def _nearby_unit_qty(text: str, span: tuple[int, int]) -> Decimal | None:
    window = text[span[1] : span[1] + 48]
    match = QTY_UNIT_RE.search(window)
    if match:
        return parse_amount(match.group(1))
    return None


def extract_items(text: str) -> list[LineItem]:
    prices = _price_entries(text)
    qtys = _qty_mentions(text)
    used_qty: set[int] = set()

    def match_qty(name: str) -> Decimal | None:
        for index, (qty, qname, _span) in enumerate(qtys):
            if index in used_qty:
                continue
            if _names_match(name, qname):
                used_qty.add(index)
                return qty
        return None

    tentative: list[tuple[dict, Decimal | None]] = []
    for entry in prices:
        qty = entry["quantity"]
        if qty is None:
            qty = match_qty(entry["name"])
        if qty is None:
            qty = _nearby_unit_qty(text, entry["span"])
        tentative.append((entry, qty))

    skip: set[int] = set()
    for i, (entry, qty) in enumerate(tentative):
        price = entry["unit_price_ngn"]
        for j, (other, other_qty) in enumerate(tentative):
            if i == j:
                continue
            if not _names_match(entry["name"], other["name"]):
                continue
            other_unit = other["unit_price_ngn"]
            if other_qty and other_qty > 1 and money(price) == money(other_qty * other_unit):
                skip.add(i)
            if qty and qty > 1 and money(other_unit) == money(qty * price):
                skip.add(j)

    items: list[LineItem] = []
    for index, (entry, qty) in enumerate(tentative):
        if index in skip:
            continue
        if qty is None:
            qty = Decimal("1")
        items.append(
            LineItem(name=entry["name"], quantity=qty, unit_price_ngn=entry["unit_price_ngn"])
        )
    return items


class HeuristicExtractor:
    name = "heuristic"

    def extract(self, text: str) -> ProposedOrder:
        cleaned = text.strip()
        email = _extract_email(cleaned)
        name = _extract_name(cleaned, email)
        stated_total = _extract_total(cleaned)
        items = extract_items(cleaned)
        return ProposedOrder(
            buyer_name=name,
            buyer_email=email,
            items=items,
            stated_total_ngn=stated_total,
            notes="",
            source=self.name,
            raw_text=cleaned,
        )
