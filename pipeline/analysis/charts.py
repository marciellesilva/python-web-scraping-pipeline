"""Geração dos gráficos em PNG com Matplotlib."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem interface gráfica (funciona em servidores/CI)

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

PRIMARY = "#4C72B0"
ACCENT = "#DD8452"


def _finish(fig: plt.Figure, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=120)
    plt.close(fig)
    return output


def plot_price_by_category(stats: pd.DataFrame, output: Path, top: int = 15) -> Path:
    """Barras horizontais com o preço médio das ``top`` categorias mais caras."""
    data = stats.head(top).sort_values("mean")
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(data.index, data["mean"], color=PRIMARY)
    ax.bar_label(bars, labels=[f"£{v:.2f}" for v in data["mean"]], padding=3, fontsize=8)
    ax.set_title(f"Preço médio por categoria (top {top})")
    ax.set_xlabel("Preço médio (£)")
    ax.set_xlim(0, data["mean"].max() * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    return _finish(fig, output)


def plot_rating_distribution(distribution: pd.Series, output: Path) -> Path:
    """Barras verticais com a quantidade de livros por nota."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = [f"{'★' * int(r)}" for r in distribution.index]
    bars = ax.bar(labels, distribution.values, color=ACCENT)
    ax.bar_label(bars, padding=3)
    ax.set_title("Distribuição das avaliações dos livros")
    ax.set_xlabel("Avaliação")
    ax.set_ylabel("Quantidade de livros")
    ax.set_ylim(0, distribution.max() * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    return _finish(fig, output)


def plot_top_counts(counts: pd.Series, title: str, xlabel: str, output: Path) -> Path:
    """Gráfico genérico de ranking (usado para tags e autores)."""
    data = counts.sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(data.index.astype(str), data.values, color=PRIMARY)
    ax.bar_label(bars, padding=3)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_xlim(0, data.max() * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    return _finish(fig, output)
