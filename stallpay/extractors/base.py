"""Extractor interface: chat text in, a proposed order out."""
from __future__ import annotations

from typing import Protocol

from ..models import ProposedOrder


class OrderExtractor(Protocol):
    name: str

    def extract(self, text: str) -> ProposedOrder:
        """Return a proposed order. Never talks to PayPal."""
        ...
