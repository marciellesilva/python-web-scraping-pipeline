"""Funções puras de limpeza e normalização de dados.

Todas as funções aqui são determinísticas e sem efeitos colaterais, o que
facilita os testes unitários e o reaproveitamento entre os scrapers.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from urllib.parse import urljoin

# O books.toscrape.com representa a avaliação como uma classe CSS por extenso
# (ex.: ``<p class="star-rating Three">``).
RATING_WORDS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

_PRICE_RE = re.compile(r"(\d+(?:[.,]\d+)?)")
_STOCK_COUNT_RE = re.compile(r"\((\d+)\s+available\)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
# Aspas tipográficas usadas pelo quotes.toscrape.com ao redor das citações.
_QUOTE_CHARS = "\u201c\u201d\"'"


def normalize_whitespace(text: str | None) -> str:
    """Colapsa espaços/quebras de linha consecutivos e remove bordas."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def parse_price(raw: str | None) -> float | None:
    """Converte textos como ``"£51.77"`` ou ``"Â£51.77"`` em ``51.77``.

    Retorna ``None`` quando nenhum número é encontrado.
    """
    if not raw:
        return None
    match = _PRICE_RE.search(raw)
    if not match:
        return None
    return round(float(match.group(1).replace(",", ".")), 2)


def parse_rating(raw: str | Iterable[str] | None) -> int | None:
    """Extrai a nota (0–5) a partir da classe CSS ``star-rating``.

    Aceita tanto a string completa (``"star-rating Three"``) quanto uma lista
    de classes (``["star-rating", "Three"]``).
    """
    if not raw:
        return None
    tokens = raw.split() if isinstance(raw, str) else list(raw)
    for token in tokens:
        value = RATING_WORDS.get(token.strip().lower())
        if value is not None:
            return value
    return None


def parse_availability(raw: str | None) -> tuple[bool, int | None]:
    """Interpreta o texto de disponibilidade.

    ``"In stock (22 available)"`` → ``(True, 22)``
    ``"In stock"`` → ``(True, None)``
    ``"Out of stock"`` → ``(False, 0)``
    """
    text = normalize_whitespace(raw).lower()
    if not text:
        return False, None
    if "out of stock" in text:
        return False, 0
    in_stock = "in stock" in text
    match = _STOCK_COUNT_RE.search(text)
    count = int(match.group(1)) if match else None
    return in_stock, count


def clean_quote_text(raw: str | None) -> str:
    """Remove aspas tipográficas e normaliza espaços de uma citação."""
    return normalize_whitespace(raw).strip(_QUOTE_CHARS).strip()


def clean_tags(tags: Iterable[str] | None) -> list[str]:
    """Normaliza tags: minúsculas, sem espaços extras, sem duplicatas.

    A ordem original de aparição é preservada.
    """
    seen: dict[str, None] = {}
    for tag in tags or []:
        normalized = normalize_whitespace(tag).lower()
        if normalized:
            seen.setdefault(normalized, None)
    return list(seen)


def absolute_url(base: str, href: str | None) -> str:
    """Resolve um link relativo em relação à URL da página."""
    return urljoin(base, href or "")
