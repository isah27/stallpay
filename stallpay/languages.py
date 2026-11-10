"""Buyer-facing languages. English is the default until the buyer picks another."""
from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "es", "hi", "pcm", "fr")

LANGUAGE_LABELS = {
    "en": "English",
    "es": "Español",
    "hi": "हिन्दी",
    "pcm": "Pidgin",
    "fr": "Français",
}

_ALIASES = {
    "english": "en",
    "en-gb": "en",
    "en-us": "en",
    "spanish": "es",
    "espanol": "es",
    "español": "es",
    "castellano": "es",
    "hindi": "hi",
    "hinglish": "hi",
    "hi-in": "hi",
    "pidgin": "pcm",
    "naija": "pcm",
    "nigerian pidgin": "pcm",
    "french": "fr",
    "francais": "fr",
    "français": "fr",
    "fr-fr": "fr",
}


def normalize_language(value: str | None, default: str = "en") -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return default
    if raw in SUPPORTED_LANGUAGES:
        return raw
    return _ALIASES.get(raw, default)
