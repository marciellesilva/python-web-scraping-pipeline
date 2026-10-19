"""Utilitários de exportação compartilhados pelos scrapers de citações."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

QUOTE_FIELDS = ["quote", "author", "tags", "author_url"]
TAG_SEPARATOR = "|"


def quotes_to_dataframe(quotes: list[dict]) -> pd.DataFrame:
    """Converte a lista de citações em DataFrame (tags como texto ``a|b|c``)."""
    df = pd.DataFrame(quotes, columns=QUOTE_FIELDS)
    df["tags"] = df["tags"].apply(lambda tags: TAG_SEPARATOR.join(tags or []))
    return df


def export_quotes(quotes: list[dict], csv_path: Path, json_path: Path) -> None:
    """Salva as citações em CSV (tags unidas por ``|``) e JSON (tags em lista)."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    quotes_to_dataframe(quotes).to_csv(csv_path, index=False, encoding="utf-8")
    json_path.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("%d citações exportadas para %s e %s", len(quotes), csv_path, json_path)
