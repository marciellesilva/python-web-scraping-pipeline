"""Parsing de páginas do quotes.toscrape.com com BeautifulSoup.

O mesmo parser é reutilizado pelos dois scrapers:

* ``bs4_scraper``: HTML baixado com ``requests``;
* ``selenium_scraper``: HTML já renderizado pelo navegador (``page_source``).
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from pipeline.cleaning import absolute_url, clean_quote_text, clean_tags, normalize_whitespace

# ``lxml`` é mais rápido; caso não esteja instalado, usamos o parser nativo.
try:
    import lxml  # noqa: F401

    HTML_PARSER = "lxml"
except ImportError:  # pragma: no cover - depende do ambiente
    HTML_PARSER = "html.parser"


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, HTML_PARSER)


def parse_quotes(html: str, page_url: str) -> list[dict]:
    """Extrai todas as citações de uma página.

    Cada citação vira um dicionário com ``quote``, ``author``, ``tags``
    (lista) e ``author_url`` (quando o link "(about)" existe).
    """
    soup = make_soup(html)
    quotes = []
    for block in soup.select("div.quote"):
        text_el = block.select_one("span.text")
        author_el = block.select_one("small.author")
        if text_el is None or author_el is None:
            continue  # bloco incompleto: ignora em vez de quebrar o pipeline
        about = block.select_one("a[href*='/author/']")
        quotes.append(
            {
                "quote": clean_quote_text(text_el.get_text()),
                "author": normalize_whitespace(author_el.get_text()),
                "tags": clean_tags(tag.get_text() for tag in block.select("a.tag")),
                "author_url": absolute_url(page_url, about["href"]) if about else "",
            }
        )
    return quotes


def parse_next_page(html: str, page_url: str) -> str | None:
    """URL absoluta da próxima página, ou ``None`` na última página."""
    link = make_soup(html).select_one("li.next a")
    return absolute_url(page_url, link["href"]) if link and link.get("href") else None
