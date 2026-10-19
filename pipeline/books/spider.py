"""Spider que percorre todo o catálogo do books.toscrape.com.

Estratégia de crawling:

1. Abre a página inicial e lê a lista de categorias da barra lateral.
2. Visita cada categoria e extrai os livros da listagem.
3. Segue a paginação ("next") dentro de cada categoria até a última página.

Assim o campo ``category`` é obtido direto da listagem, sem precisar abrir
as 1.000 páginas de detalhe — menos requisições e um crawl mais educado.
"""

from __future__ import annotations

from collections.abc import Iterator

import scrapy
from scrapy.http import Response

from pipeline.books import parsers
from pipeline.books.items import BookItem
from pipeline.config import BOOKS_BASE_URL


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = [BOOKS_BASE_URL]

    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Página inicial: agenda uma requisição por categoria."""
        categories = parsers.parse_category_links(response, response.url)
        self.logger.info("Encontradas %d categorias", len(categories))
        for name, url in categories:
            yield scrapy.Request(url, callback=self.parse_category, cb_kwargs={"category": name})

    def parse_category(
        self, response: Response, category: str
    ) -> Iterator[BookItem | scrapy.Request]:
        """Página de listagem: emite os livros e segue a paginação."""
        for raw in parsers.parse_book_cards(response, response.url, category):
            yield BookItem(**raw)

        next_url = parsers.parse_next_page(response, response.url)
        if next_url:
            yield response.follow(
                next_url, callback=self.parse_category, cb_kwargs={"category": category}
            )
