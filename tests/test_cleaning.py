"""Testes das funções puras de limpeza (``pipeline.cleaning``)."""

import pytest

from pipeline import cleaning


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("£51.77", 51.77),
        ("Â£51.77", 51.77),  # erro clássico de encoding (UTF-8 lido como Latin-1)
        ("  £ 10.00 ", 10.0),
        ("12,5", 12.5),
        ("£7", 7.0),
        ("", None),
        (None, None),
        ("grátis", None),
    ],
)
def test_parse_price(raw, expected):
    assert cleaning.parse_price(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("star-rating Three", 3),
        ("star-rating One", 1),
        ("star-rating Five", 5),
        (["star-rating", "Four"], 4),
        ("star-rating two", 2),
        ("star-rating", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_rating(raw, expected):
    assert cleaning.parse_rating(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("In stock (22 available)", (True, 22)),
        ("\n   In stock\n  ", (True, None)),
        ("Out of stock", (False, 0)),
        ("", (False, None)),
        (None, (False, None)),
    ],
)
def test_parse_availability(raw, expected):
    assert cleaning.parse_availability(raw) == expected


def test_normalize_whitespace_collapses_spaces_and_newlines():
    assert cleaning.normalize_whitespace("  A \n Light\t in   the Attic ") == "A Light in the Attic"


def test_normalize_whitespace_handles_empty_values():
    assert cleaning.normalize_whitespace(None) == ""
    assert cleaning.normalize_whitespace("   ") == ""


def test_clean_quote_text_removes_typographic_quotes():
    raw = "\u201c  The world as we have created it is a process of our thinking. \u201d"
    assert cleaning.clean_quote_text(raw) == (
        "The world as we have created it is a process of our thinking."
    )


def test_clean_tags_lowercases_and_deduplicates_preserving_order():
    assert cleaning.clean_tags(["Love", " life ", "love", "", "Inspirational"]) == [
        "love",
        "life",
        "inspirational",
    ]


def test_clean_tags_accepts_none():
    assert cleaning.clean_tags(None) == []


def test_absolute_url_resolves_relative_links():
    base = "https://books.toscrape.com/catalogue/page-2.html"
    assert cleaning.absolute_url(base, "page-3.html") == (
        "https://books.toscrape.com/catalogue/page-3.html"
    )
    assert cleaning.absolute_url(base, "../index.html") == "https://books.toscrape.com/index.html"
