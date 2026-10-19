"""Definição do item ``BookItem`` usado pelo spider e pelos pipelines."""

from __future__ import annotations

import scrapy


class BookItem(scrapy.Item):
    """Representa um livro extraído do catálogo.

    Os campos chegam "crus" do spider e são normalizados em
    :class:`pipeline.books.pipelines.CleanBookPipeline`.
    """

    title = scrapy.Field()
    price = scrapy.Field()  # float, em libras (GBP)
    rating = scrapy.Field()  # int de 1 a 5
    availability = scrapy.Field()  # texto original, ex.: "In stock"
    in_stock = scrapy.Field()  # bool derivado de ``availability``
    category = scrapy.Field()
    url = scrapy.Field()
