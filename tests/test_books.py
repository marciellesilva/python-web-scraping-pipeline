"""Testes do spider Scrapy, dos parsers e dos item pipelines de livros."""

import pytest
from parsel import Selector
from scrapy.exceptions import DropItem
from scrapy.http import HtmlResponse, Request

from pipeline.books import parsers
from pipeline.books.items import BookItem
from pipeline.books.pipelines import CleanBookPipeline, DuplicatesPipeline
from pipeline.books.spider import BooksSpider
from tests.conftest import BOOKS_HOME_URL, BOOKS_MYSTERY_P2_URL


def make_response(url: str, html: str, **cb_kwargs) -> HtmlResponse:
    """Cria uma resposta Scrapy "falsa" a partir do HTML salvo."""
    request = Request(url, cb_kwargs=cb_kwargs)
    return HtmlResponse(url=url, body=html, encoding="utf-8", request=request)


# --- parsers ---------------------------------------------------------------


def test_parse_category_links_returns_all_50_categories(books_home_html):
    links = parsers.parse_category_links(Selector(books_home_html), BOOKS_HOME_URL)

    assert len(links) == 50
    assert links[0] == (
        "Travel",
        "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
    )
    # A categoria raiz "Books" (que agrupa todas) não deve aparecer.
    assert "Books" not in {name for name, _ in links}


def test_parse_book_cards_extracts_raw_fields(books_home_html):
    cards = parsers.parse_book_cards(Selector(books_home_html), BOOKS_HOME_URL, "Poetry")

    assert len(cards) == 20
    first = cards[0]
    assert first["title"] == "A Light in the Attic"
    assert first["price"] == "£51.77"
    assert first["rating"] == "star-rating Three"
    assert "In stock" in first["availability"]
    assert first["category"] == "Poetry"
    assert first["url"] == (
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )


def test_parse_book_cards_uses_full_title_attribute(books_home_html):
    titles = [c["title"] for c in parsers.parse_book_cards(Selector(books_home_html), "u", "x")]
    # O texto visível é truncado com "...", mas o atributo title é completo.
    assert not any(title.endswith("...") for title in titles)


def test_parse_next_page_on_first_and_last_page(books_home_html, books_category_last_page_html):
    assert parsers.parse_next_page(Selector(books_home_html), BOOKS_HOME_URL) == (
        "https://books.toscrape.com/catalogue/page-2.html"
    )
    assert parsers.parse_next_page(Selector(books_category_last_page_html), "u") is None


def test_parse_category_name(books_category_last_page_html):
    assert parsers.parse_category_name(Selector(books_category_last_page_html)) == "Mystery"


# --- spider ----------------------------------------------------------------


def test_spider_parse_schedules_one_request_per_category(books_home_html):
    spider = BooksSpider()
    requests = list(spider.parse(make_response(BOOKS_HOME_URL, books_home_html)))

    assert len(requests) == 50
    assert all(isinstance(r, Request) for r in requests)
    assert requests[0].cb_kwargs == {"category": "Travel"}


def test_spider_parse_category_yields_items_without_next_on_last_page(
    books_category_last_page_html,
):
    spider = BooksSpider()
    response = make_response(BOOKS_MYSTERY_P2_URL, books_category_last_page_html)
    results = list(spider.parse_category(response, category="Mystery"))

    items = [r for r in results if isinstance(r, BookItem)]
    follow_ups = [r for r in results if isinstance(r, Request)]
    assert len(items) == 12  # a categoria Mystery tem 32 livros: 20 + 12
    assert follow_ups == []
    assert {item["category"] for item in items} == {"Mystery"}


def test_spider_parse_category_follows_pagination(books_home_html):
    spider = BooksSpider()
    results = list(
        spider.parse_category(make_response(BOOKS_HOME_URL, books_home_html), category="All")
    )
    follow_ups = [r for r in results if isinstance(r, Request)]

    assert len(follow_ups) == 1
    assert follow_ups[0].url == "https://books.toscrape.com/catalogue/page-2.html"
    assert follow_ups[0].cb_kwargs == {"category": "All"}


# --- pipelines -------------------------------------------------------------


def raw_item(**overrides) -> BookItem:
    data = {
        "title": "  A Light in the Attic ",
        "price": "Â£51.77",
        "rating": "star-rating Three",
        "availability": "\n    In stock\n  ",
        "category": " Poetry ",
        "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    }
    data.update(overrides)
    return BookItem(**data)


def test_clean_pipeline_normalizes_fields():
    item = CleanBookPipeline().process_item(raw_item())

    assert item["title"] == "A Light in the Attic"
    assert item["price"] == 51.77
    assert item["rating"] == 3
    assert item["availability"] == "In stock"
    assert item["in_stock"] is True
    assert item["category"] == "Poetry"


def test_clean_pipeline_marks_out_of_stock():
    item = CleanBookPipeline().process_item(raw_item(availability="Out of stock"))
    assert item["in_stock"] is False


@pytest.mark.parametrize("overrides", [{"title": "   "}, {"price": "sem preço"}])
def test_clean_pipeline_drops_invalid_items(overrides):
    with pytest.raises(DropItem):
        CleanBookPipeline().process_item(raw_item(**overrides))


def test_duplicates_pipeline_drops_repeated_urls():
    pipeline = DuplicatesPipeline()
    pipeline.process_item(raw_item())
    with pytest.raises(DropItem):
        pipeline.process_item(raw_item(title="Outro título"))


def test_full_flow_from_html_to_clean_items(books_category_last_page_html):
    """Integração: HTML → spider → pipelines, como no crawl real."""
    spider = BooksSpider()
    response = make_response(BOOKS_MYSTERY_P2_URL, books_category_last_page_html)
    clean, dedup = CleanBookPipeline(), DuplicatesPipeline()

    items = [
        dedup.process_item(clean.process_item(r))
        for r in spider.parse_category(response, category="Mystery")
        if isinstance(r, BookItem)
    ]

    assert len(items) == 12
    assert all(isinstance(i["price"], float) and i["price"] > 0 for i in items)
    assert all(1 <= i["rating"] <= 5 for i in items)
