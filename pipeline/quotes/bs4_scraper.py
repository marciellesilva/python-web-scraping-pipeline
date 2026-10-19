"""Scraper do quotes.toscrape.com usando ``requests`` + BeautifulSoup."""

from __future__ import annotations

import logging
import time

import requests

from pipeline.config import QUOTES_BASE_URL, REQUEST_DELAY, REQUEST_TIMEOUT, USER_AGENT
from pipeline.quotes.parsers import parse_next_page, parse_quotes

logger = logging.getLogger(__name__)


def build_session() -> requests.Session:
    """Sessão HTTP reutilizável (keep-alive) com User-Agent identificável."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def scrape_quotes(
    start_url: str = QUOTES_BASE_URL,
    session: requests.Session | None = None,
    max_pages: int | None = None,
    delay: float = REQUEST_DELAY,
) -> list[dict]:
    """Percorre todas as páginas seguindo o botão "Next".

    :param start_url: primeira página a visitar.
    :param session: sessão HTTP (injetável para facilitar testes).
    :param max_pages: limite opcional de páginas (útil para execuções rápidas).
    :param delay: pausa entre requisições, para não sobrecarregar o servidor.
    """
    session = session or build_session()
    url: str | None = start_url
    quotes: list[dict] = []
    page = 0

    while url and (max_pages is None or page < max_pages):
        page += 1
        logger.debug("Baixando página %d: %s", page, url)
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        page_quotes = parse_quotes(response.text, url)
        quotes.extend(page_quotes)
        logger.info("Página %d: %d citações", page, len(page_quotes))

        url = parse_next_page(response.text, url)
        if url and delay:
            time.sleep(delay)

    logger.info("Total (BeautifulSoup): %d citações em %d páginas", len(quotes), page)
    return quotes
