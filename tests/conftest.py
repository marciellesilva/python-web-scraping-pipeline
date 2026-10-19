"""Fixtures compartilhadas pelos testes (HTML salvo em disco, sem rede)."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

BOOKS_HOME_URL = "https://books.toscrape.com/index.html"
BOOKS_MYSTERY_P2_URL = "https://books.toscrape.com/catalogue/category/books/mystery_3/page-2.html"


def read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def books_home_html() -> str:
    return read_fixture("books_home.html")


@pytest.fixture
def books_category_last_page_html() -> str:
    return read_fixture("books_category_last_page.html")


@pytest.fixture
def quotes_page_1_html() -> str:
    return read_fixture("quotes_page_1.html")


@pytest.fixture
def quotes_last_page_html() -> str:
    return read_fixture("quotes_last_page.html")


@pytest.fixture
def quotes_js_rendered_html() -> str:
    return read_fixture("quotes_js_rendered.html")
