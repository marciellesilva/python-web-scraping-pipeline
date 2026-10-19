"""Funções de parsing do books.toscrape.com, independentes do spider.

Mantê-las separadas do spider permite testá-las com HTML salvo em disco,
sem rede e sem precisar iniciar o motor do Scrapy.
"""

from __future__ import annotations

from parsel import Selector

from pipeline.cleaning import absolute_url, normalize_whitespace


def parse_category_links(selector: Selector, page_url: str) -> list[tuple[str, str]]:
    """Retorna ``(nome_da_categoria, url_absoluta)`` da barra lateral.

    A barra lateral tem uma lista aninhada: o item raiz é "Books" (que agrupa
    tudo) e os itens internos são as categorias reais. Usamos apenas os
    internos para não duplicar livros.
    """
    links = []
    for anchor in selector.css("div.side_categories ul li ul li a"):
        name = normalize_whitespace(anchor.css("::text").get())
        href = anchor.attrib.get("href")
        if name and href:
            links.append((name, absolute_url(page_url, href)))
    return links


def parse_category_name(selector: Selector) -> str:
    """Nome da categoria exibido no cabeçalho da página de listagem."""
    return normalize_whitespace(selector.css("div.page-header h1::text").get())


def parse_book_cards(selector: Selector, page_url: str, category: str) -> list[dict]:
    """Extrai os dados brutos de cada ``article.product_pod`` da página."""
    books = []
    for card in selector.css("article.product_pod"):
        link = card.css("h3 a")
        books.append(
            {
                # O texto do link é truncado ("..."); o atributo title é completo.
                "title": link.attrib.get("title") or link.css("::text").get(),
                "price": card.css("p.price_color::text").get(),
                "rating": card.css("p.star-rating").attrib.get("class"),
                "availability": " ".join(card.css("p.availability ::text").getall()),
                "category": category,
                "url": absolute_url(page_url, link.attrib.get("href")),
            }
        )
    return books


def parse_next_page(selector: Selector, page_url: str) -> str | None:
    """URL absoluta da próxima página de listagem, ou ``None`` se for a última."""
    href = selector.css("li.next a::attr(href)").get()
    return absolute_url(page_url, href) if href else None
