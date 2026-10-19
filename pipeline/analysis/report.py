"""Orquestra a etapa de análise: lê os CSVs, calcula métricas e salva relatórios."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from pipeline.analysis import charts, metrics
from pipeline.config import BOOKS_CSV, QUOTES_CSV, QUOTES_JS_CSV

logger = logging.getLogger(__name__)


def _markdown_table(df: pd.DataFrame | pd.Series) -> str:
    """Converte um DataFrame/Series em tabela Markdown (sem depender do ``tabulate``)."""
    frame = df.to_frame() if isinstance(df, pd.Series) else df
    frame = frame.reset_index()
    header = "| " + " | ".join(map(str, frame.columns)) + " |"
    divider = "|" + "|".join(" --- " for _ in frame.columns) + "|"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, divider, *rows])


def analyze_books(csv_path: Path, reports_dir: Path) -> list[str]:
    """Gera métricas e gráficos dos livros; devolve as seções do relatório."""
    books = metrics.load_books(csv_path)
    summary = metrics.books_summary(books)
    stats = metrics.price_stats_by_category(books)
    distribution = metrics.rating_distribution(books)
    by_rating = metrics.price_by_rating(books)

    stats.to_csv(reports_dir / "price_stats_by_category.csv")
    distribution.to_csv(reports_dir / "rating_distribution.csv")
    charts.plot_price_by_category(stats, reports_dir / "price_by_category.png")
    charts.plot_rating_distribution(distribution, reports_dir / "rating_distribution.png")

    logger.info("Livros: %s", summary)
    return [
        "## Livros (books.toscrape.com)",
        "\n".join(f"- **{key}**: {value}" for key, value in summary.items()),
        "### Top 10 categorias por preço médio (£)",
        _markdown_table(stats.head(10)),
        "### Distribuição de avaliações",
        _markdown_table(distribution),
        "### Preço médio por avaliação (£)",
        _markdown_table(by_rating),
        "![Preço por categoria](price_by_category.png)",
        "![Distribuição de avaliações](rating_distribution.png)",
    ]


def analyze_quotes(csv_path: Path, reports_dir: Path) -> list[str]:
    """Gera rankings de tags e autores; devolve as seções do relatório."""
    quotes = metrics.load_quotes(csv_path)
    tags = metrics.top_tags(quotes)
    authors = metrics.top_authors(quotes)

    tags.to_csv(reports_dir / "top_tags.csv")
    authors.to_csv(reports_dir / "top_authors.csv")
    charts.plot_top_counts(tags, "Top 10 tags", "Citações", reports_dir / "top_tags.png")
    charts.plot_top_counts(authors, "Top 10 autores", "Citações", reports_dir / "top_authors.png")

    logger.info("Citações: %d registros, %d autores", len(quotes), quotes["author"].nunique())
    return [
        "## Citações (quotes.toscrape.com)",
        f"- **total_quotes**: {len(quotes)}\n- **authors**: {quotes['author'].nunique()}",
        "### Top 10 tags",
        _markdown_table(tags),
        "### Top 10 autores",
        _markdown_table(authors),
        "![Top tags](top_tags.png)",
        "![Top autores](top_authors.png)",
    ]


def run_analysis(data_dir: Path, reports_dir: Path) -> Path | None:
    """Executa a análise com os dados disponíveis e grava ``reports/summary.md``.

    Cada fonte é opcional: se o CSV não existir, a seção é pulada com aviso.
    Retorna o caminho do resumo, ou ``None`` se não houver nada para analisar.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    sections: list[str] = []

    books_csv = data_dir / BOOKS_CSV
    if books_csv.exists():
        sections += analyze_books(books_csv, reports_dir)
    else:
        logger.warning("%s não encontrado — rode 'scrape-books' antes.", books_csv)

    # Prefere os dados do scraper estático; usa os do Selenium como alternativa.
    quotes_csv = next(
        (p for p in (data_dir / QUOTES_CSV, data_dir / QUOTES_JS_CSV) if p.exists()), None
    )
    if quotes_csv:
        sections += analyze_quotes(quotes_csv, reports_dir)
    else:
        logger.warning("Nenhum CSV de citações encontrado — rode 'scrape-quotes' antes.")

    if not sections:
        return None

    summary_path = reports_dir / "summary.md"
    header = [
        "# Relatório — Web Scraping Pipeline",
        f"_Gerado em {datetime.now():%Y-%m-%d %H:%M}_",
    ]
    summary_path.write_text("\n\n".join(header + sections) + "\n", encoding="utf-8")
    logger.info("Relatório salvo em %s", summary_path)
    return summary_path
