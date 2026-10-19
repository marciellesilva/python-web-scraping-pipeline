"""Métricas calculadas com Pandas sobre livros e citações.

As funções recebem e devolvem ``DataFrame``/``Series``, sem ler ou gravar
arquivos, para que possam ser testadas com dados sintéticos.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.quotes.export import TAG_SEPARATOR

# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------


def load_books(csv_path: Path) -> pd.DataFrame:
    """Lê o CSV de livros garantindo os tipos numéricos corretos."""
    df = pd.read_csv(csv_path)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    return df.dropna(subset=["price"])


def load_quotes(csv_path: Path) -> pd.DataFrame:
    """Lê o CSV de citações convertendo a coluna ``tags`` de volta para lista."""
    df = pd.read_csv(csv_path, keep_default_na=False)
    df["tags"] = df["tags"].apply(split_tags)
    return df


def split_tags(value: str | list | None) -> list[str]:
    """``"love|life"`` → ``["love", "life"]`` (aceita listas já prontas)."""
    if isinstance(value, list):
        return value
    if not value or not isinstance(value, str):
        return []
    return [tag for tag in value.split(TAG_SEPARATOR) if tag]


# ---------------------------------------------------------------------------
# Livros
# ---------------------------------------------------------------------------


def price_stats_by_category(books: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas de preço por categoria, ordenadas pelo preço médio."""
    stats = (
        books.groupby("category")["price"]
        .agg(books="count", mean="mean", median="median", min="min", max="max")
        .round(2)
        .sort_values("mean", ascending=False)
    )
    return stats


def rating_distribution(books: pd.DataFrame) -> pd.Series:
    """Quantidade de livros por nota (1 a 5), incluindo notas sem livros."""
    counts = books["rating"].value_counts().reindex(range(1, 6), fill_value=0)
    counts.index.name = "rating"
    counts.name = "books"
    return counts.astype(int)


def price_by_rating(books: pd.DataFrame) -> pd.Series:
    """Preço médio por nota — ajuda a ver se livros melhor avaliados são mais caros."""
    return books.groupby("rating")["price"].mean().round(2).rename("mean_price")


def books_summary(books: pd.DataFrame) -> dict:
    """Indicadores gerais do catálogo."""
    return {
        "total_books": int(len(books)),
        "categories": int(books["category"].nunique()),
        "mean_price": round(float(books["price"].mean()), 2),
        "median_price": round(float(books["price"].median()), 2),
        "mean_rating": round(float(books["rating"].mean()), 2),
        "in_stock_pct": round(float(books["in_stock"].astype(bool).mean() * 100), 1),
    }


# ---------------------------------------------------------------------------
# Citações
# ---------------------------------------------------------------------------


def top_tags(quotes: pd.DataFrame, n: int = 10) -> pd.Series:
    """As ``n`` tags mais frequentes."""
    exploded = quotes["tags"].explode().dropna()
    exploded = exploded[exploded != ""]
    counts = exploded.value_counts().head(n)
    counts.index.name = "tag"
    counts.name = "quotes"
    return counts


def top_authors(quotes: pd.DataFrame, n: int = 10) -> pd.Series:
    """Os ``n`` autores com mais citações."""
    counts = quotes["author"].value_counts().head(n)
    counts.index.name = "author"
    counts.name = "quotes"
    return counts
