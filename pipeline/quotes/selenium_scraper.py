"""Scraper do https://quotes.toscrape.com/js/ usando Selenium.

Nessa versão do site as citações são inseridas na página via JavaScript,
portanto um simples ``requests.get`` não as enxerga. O Selenium abre um
Chrome *headless*, espera o conteúdo ser renderizado e clica em "Next" até a
última página. O HTML renderizado é então processado pelo mesmo parser
BeautifulSoup usado no scraper estático.

O driver é obtido automaticamente pelo **Selenium Manager** (Selenium >= 4.6),
sem necessidade de baixar o ChromeDriver manualmente. Se o Chrome não estiver
disponível na máquina, o scraper registra um aviso e retorna uma lista vazia,
sem interromper o restante do pipeline.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from pipeline.config import QUOTES_JS_URL, REQUEST_TIMEOUT, USER_AGENT
from pipeline.quotes.parsers import parse_quotes

logger = logging.getLogger(__name__)

# Desativa o envio de estatísticas anônimas do Selenium Manager.
os.environ.setdefault("SE_AVOID_STATS", "true")


def create_chrome_driver(headless: bool = True) -> WebDriver:
    """Cria uma instância do Chrome configurada para scraping."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")  # necessário em containers/CI
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument(f"--user-agent={USER_AGENT}")
    return webdriver.Chrome(options=options)


def _wait_for_quotes(driver: WebDriver, timeout: int) -> None:
    """Bloqueia até que o JavaScript tenha renderizado as citações."""
    WebDriverWait(driver, timeout).until(
        ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div.quote"))
    )


def scrape_quotes_js(
    start_url: str = QUOTES_JS_URL,
    max_pages: int | None = None,
    headless: bool = True,
    driver_factory: Callable[..., WebDriver] = create_chrome_driver,
    timeout: int = REQUEST_TIMEOUT,
) -> list[dict]:
    """Coleta as citações da versão JavaScript do site.

    :param driver_factory: função que cria o WebDriver (injetável em testes).
    :returns: lista de citações; vazia se o navegador não puder ser iniciado.
    """
    try:
        driver = driver_factory(headless=headless)
    except WebDriverException as exc:
        detail = str(exc).strip().splitlines()
        logger.warning(
            "Selenium indisponível (Chrome/driver não encontrado). "
            "Etapa JavaScript ignorada. Detalhe: %s",
            detail[0] if detail else type(exc).__name__,
        )
        return []

    quotes: list[dict] = []
    page = 0
    try:
        driver.get(start_url)
        while max_pages is None or page < max_pages:
            _wait_for_quotes(driver, timeout)
            page += 1
            page_quotes = parse_quotes(driver.page_source, driver.current_url)
            quotes.extend(page_quotes)
            logger.info("Página JS %d: %d citações", page, len(page_quotes))

            try:
                next_link = driver.find_element(By.CSS_SELECTOR, "li.next a")
            except NoSuchElementException:
                break  # última página

            # Guarda uma referência à primeira citação para detectar a troca
            # de página depois do clique (evita ler a página antiga).
            first_quote = driver.find_element(By.CSS_SELECTOR, "div.quote")
            next_link.click()
            WebDriverWait(driver, timeout).until(ec.staleness_of(first_quote))
    except TimeoutException:
        logger.error("Tempo esgotado aguardando a renderização em %s", driver.current_url)
    finally:
        driver.quit()

    logger.info("Total (Selenium): %d citações em %d páginas", len(quotes), page)
    return quotes
