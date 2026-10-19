"""Baixa (ou atualiza) as páginas HTML usadas como fixtures nos testes.

Uso::

    python scripts/update_fixtures.py

Os testes nunca acessam a rede: eles leem apenas os arquivos salvos em
``tests/fixtures``. Este script existe para documentar a origem desses
arquivos e permitir regerá-los caso o layout dos sites mude.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.config import USER_AGENT  # noqa: E402

FIXTURES_DIR = ROOT / "tests" / "fixtures"

PAGES = {
    "books_home.html": "https://books.toscrape.com/index.html",
    "books_category_last_page.html": (
        "https://books.toscrape.com/catalogue/category/books/mystery_3/page-2.html"
    ),
    "quotes_page_1.html": "https://quotes.toscrape.com/",
    "quotes_last_page.html": "https://quotes.toscrape.com/page/10/",
}


def download_static_pages() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    for filename, url in PAGES.items():
        response = session.get(url, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"
        (FIXTURES_DIR / filename).write_text(response.text, encoding="utf-8")
        print(f"ok  {filename:<32} <- {url}")


def download_rendered_js_page() -> None:
    """Salva o HTML da versão JS *depois* da renderização (via Selenium)."""
    from selenium.common.exceptions import WebDriverException

    from pipeline.quotes.selenium_scraper import _wait_for_quotes, create_chrome_driver

    try:
        driver = create_chrome_driver()
    except WebDriverException:
        print("--  quotes_js_rendered.html: Chrome indisponível, mantendo arquivo atual")
        return
    try:
        driver.get("https://quotes.toscrape.com/js/")
        _wait_for_quotes(driver, 15)
        (FIXTURES_DIR / "quotes_js_rendered.html").write_text(driver.page_source, encoding="utf-8")
        print("ok  quotes_js_rendered.html         <- https://quotes.toscrape.com/js/ (Selenium)")
    finally:
        driver.quit()


if __name__ == "__main__":
    from pipeline.cli import use_system_certificates

    use_system_certificates()
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    download_static_pages()
    download_rendered_js_page()
