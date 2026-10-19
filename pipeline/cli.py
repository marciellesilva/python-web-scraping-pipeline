"""Interface de linha de comando do pipeline.

Exemplos::

    python -m pipeline run --all             # executa todas as etapas
    python -m pipeline run --all --no-selenium
    python -m pipeline scrape-books
    python -m pipeline scrape-quotes --engine both
    python -m pipeline analyze
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from pipeline import __version__
from pipeline.config import (
    DATA_DIR,
    QUOTES_CSV,
    QUOTES_JS_CSV,
    QUOTES_JS_JSON,
    QUOTES_JSON,
    REPORTS_DIR,
)

logger = logging.getLogger("pipeline")

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def use_system_certificates() -> None:
    """Faz o ``requests`` validar HTTPS com os certificados do sistema operacional.

    Útil em redes corporativas ou com antivírus que inspecionam HTTPS
    (proxies com certificado raiz próprio). Usa o pacote ``truststore``
    quando disponível; caso contrário, mantém o comportamento padrão.
    """
    try:
        import truststore
    except ImportError:  # pragma: no cover - dependência opcional
        return
    truststore.inject_into_ssl()


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Configura o logging no console (e opcionalmente em arquivo)."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format=LOG_FORMAT,
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    # Bibliotecas muito verbosas ficam em WARNING para não poluir a saída.
    for noisy in ("urllib3", "selenium", "matplotlib", "PIL", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    # O Scrapy é útil em INFO (estatísticas do crawl), mas não em DEBUG.
    logging.getLogger("scrapy").setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------


def step_scrape_books(args: argparse.Namespace) -> None:
    # Import tardio: o Scrapy/Twisted só é carregado quando realmente usado.
    from pipeline.books.runner import run_books_spider

    run_books_spider(args.data_dir)


def step_scrape_quotes(args: argparse.Namespace) -> None:
    from pipeline.quotes.export import export_quotes

    if args.engine in ("bs4", "both"):
        from pipeline.quotes.bs4_scraper import scrape_quotes

        quotes = scrape_quotes(max_pages=args.max_pages)
        export_quotes(quotes, args.data_dir / QUOTES_CSV, args.data_dir / QUOTES_JSON)

    if args.engine in ("selenium", "both"):
        from pipeline.quotes.selenium_scraper import scrape_quotes_js

        quotes_js = scrape_quotes_js(max_pages=args.max_pages, headless=not args.show_browser)
        if quotes_js:
            export_quotes(quotes_js, args.data_dir / QUOTES_JS_CSV, args.data_dir / QUOTES_JS_JSON)


def step_analyze(args: argparse.Namespace) -> None:
    from pipeline.analysis.report import run_analysis

    summary = run_analysis(args.data_dir, args.reports_dir)
    if summary is None:
        logger.error("Nenhum dado para analisar em %s", args.data_dir)


def step_run(args: argparse.Namespace) -> None:
    """Executa as etapas selecionadas na ordem: livros → citações → análise."""
    run_all = args.all
    if not (run_all or args.books or args.quotes or args.analyze):
        raise SystemExit("Informe --all ou ao menos uma etapa: --books, --quotes, --analyze")

    if run_all or args.books:
        step_scrape_books(args)
    if run_all or args.quotes:
        args.engine = "bs4" if args.no_selenium else "both"
        step_scrape_quotes(args)
    if run_all or args.analyze:
        step_analyze(args)


# ---------------------------------------------------------------------------
# Argumentos
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--data-dir", type=Path, default=DATA_DIR, help="pasta dos dados (padrão: data/)"
    )
    common.add_argument(
        "--reports-dir",
        type=Path,
        default=REPORTS_DIR,
        help="pasta dos relatórios e gráficos (padrão: reports/)",
    )
    common.add_argument("-v", "--verbose", action="store_true", help="logs em nível DEBUG")
    common.add_argument("--log-file", type=Path, help="também grava os logs neste arquivo")

    quotes_opts = argparse.ArgumentParser(add_help=False)
    quotes_opts.add_argument(
        "--max-pages", type=int, default=None, help="limita a quantidade de páginas de citações"
    )
    quotes_opts.add_argument(
        "--show-browser", action="store_true", help="abre o Chrome visível (sem headless)"
    )

    parser = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Pipeline de web scraping: coleta, limpeza e análise de dados.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMANDO")

    run = sub.add_parser(
        "run", parents=[common, quotes_opts], help="executa várias etapas em sequência"
    )
    run.add_argument("--all", action="store_true", help="executa todas as etapas")
    run.add_argument("--books", action="store_true", help="inclui a coleta de livros")
    run.add_argument("--quotes", action="store_true", help="inclui a coleta de citações")
    run.add_argument("--analyze", action="store_true", help="inclui a análise")
    run.add_argument("--no-selenium", action="store_true", help="pula o scraper Selenium")
    run.set_defaults(func=step_run)

    books = sub.add_parser("scrape-books", parents=[common], help="coleta o catálogo com Scrapy")
    books.set_defaults(func=step_scrape_books)

    quotes = sub.add_parser(
        "scrape-quotes", parents=[common, quotes_opts], help="coleta as citações"
    )
    quotes.add_argument(
        "--engine",
        choices=["bs4", "selenium", "both"],
        default="bs4",
        help="bs4 = requests+BeautifulSoup; selenium = versão JS (padrão: bs4)",
    )
    quotes.set_defaults(func=step_scrape_quotes)

    analyze = sub.add_parser(
        "analyze", parents=[common], help="gera estatísticas e gráficos a partir dos CSVs"
    )
    analyze.set_defaults(func=step_analyze)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose, args.log_file)
    use_system_certificates()
    started = time.perf_counter()
    logger.info("Comando '%s' iniciado", args.command)
    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.warning("Execução interrompida pelo usuário")
        return 130
    logger.info("Comando '%s' concluído em %.1fs", args.command, time.perf_counter() - started)
    return 0
