"""Execução programática do spider de livros (sem precisar de ``scrapy crawl``)."""

from __future__ import annotations

import logging
from pathlib import Path

from scrapy.crawler import CrawlerProcess

from pipeline.books.spider import BooksSpider
from pipeline.config import BOOKS_CSV, BOOKS_JSON, USER_AGENT

logger = logging.getLogger(__name__)

# Ordem dos campos nos arquivos exportados.
EXPORT_FIELDS = ["title", "category", "price", "rating", "availability", "in_stock", "url"]


def build_settings(data_dir: Path) -> dict:
    """Monta as configurações do Scrapy para este projeto.

    Os arquivos CSV/JSON são gerados pelo mecanismo de *Feed Exports* do
    Scrapy, depois que cada item passa pelos pipelines de limpeza.
    """
    return {
        "BOT_NAME": "web_scraping_pipeline",
        "USER_AGENT": USER_AGENT,
        "ROBOTSTXT_OBEY": True,
        # Crawl "educado": limite de concorrência + AutoThrottle.
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "DOWNLOAD_DELAY": 0.1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.1,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4.0,
        "RETRY_TIMES": 2,
        "ITEM_PIPELINES": {
            "pipeline.books.pipelines.CleanBookPipeline": 100,
            "pipeline.books.pipelines.DuplicatesPipeline": 200,
        },
        "FEEDS": {
            (data_dir / BOOKS_CSV): {
                "format": "csv",
                "encoding": "utf-8",
                "fields": EXPORT_FIELDS,
                "overwrite": True,
            },
            (data_dir / BOOKS_JSON): {
                "format": "json",
                "encoding": "utf-8",
                "fields": EXPORT_FIELDS,
                "indent": 2,
                "overwrite": True,
            },
        },
        # O logging é configurado pela CLI; evitamos que o Scrapy o substitua.
        "LOG_LEVEL": "INFO",
    }


def run_books_spider(data_dir: Path) -> Path:
    """Executa o crawl completo e retorna o caminho do CSV gerado.

    Observação: o reactor do Twisted só pode ser iniciado uma vez por
    processo, por isso esta função deve ser chamada no máximo uma vez.
    """
    data_dir = data_dir.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Iniciando crawl do books.toscrape.com")
    process = CrawlerProcess(build_settings(data_dir), install_root_handler=False)
    process.crawl(BooksSpider)
    process.start()
    csv_path = data_dir / BOOKS_CSV
    logger.info("Livros exportados para %s e %s", csv_path, data_dir / BOOKS_JSON)
    return csv_path
