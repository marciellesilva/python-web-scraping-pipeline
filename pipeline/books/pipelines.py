"""Item pipelines do Scrapy: validação, limpeza e deduplicação."""

from __future__ import annotations

import logging

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

from pipeline.cleaning import (
    normalize_whitespace,
    parse_availability,
    parse_price,
    parse_rating,
)

logger = logging.getLogger(__name__)


class CleanBookPipeline:
    """Normaliza os campos brutos vindos do spider.

    * ``title``/``category``: espaços normalizados
    * ``price``: ``"£51.77"`` → ``51.77`` (float)
    * ``rating``: ``"star-rating Three"`` → ``3`` (int)
    * ``availability``: texto limpo + flag booleana ``in_stock``

    Itens sem título ou sem preço válido são descartados (``DropItem``).
    """

    def process_item(self, item):
        adapter = ItemAdapter(item)

        title = normalize_whitespace(adapter.get("title"))
        if not title:
            raise DropItem(f"Livro sem título: {adapter.get('url')}")

        price = parse_price(adapter.get("price"))
        if price is None:
            raise DropItem(f"Preço inválido para {title!r}: {adapter.get('price')!r}")

        availability = normalize_whitespace(adapter.get("availability"))
        in_stock, _ = parse_availability(availability)

        adapter["title"] = title
        adapter["price"] = price
        adapter["rating"] = parse_rating(adapter.get("rating"))
        adapter["availability"] = availability
        adapter["in_stock"] = in_stock
        adapter["category"] = normalize_whitespace(adapter.get("category")) or "Unknown"
        return item


class DuplicatesPipeline:
    """Descarta livros repetidos usando a URL como chave única."""

    def __init__(self) -> None:
        self.seen_urls: set[str] = set()

    def process_item(self, item):
        url = ItemAdapter(item).get("url")
        if url in self.seen_urls:
            raise DropItem(f"Livro duplicado: {url}")
        self.seen_urls.add(url)
        return item
