"""Configurações centrais do projeto (caminhos, URLs e parâmetros de rede)."""

from __future__ import annotations

from pathlib import Path

# Raiz do repositório (um nível acima do pacote ``pipeline``).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Diretórios padrão de saída. Ambos podem ser sobrescritos pela CLI.
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

# URLs dos sites de prática.
BOOKS_BASE_URL = "https://books.toscrape.com/"
QUOTES_BASE_URL = "https://quotes.toscrape.com/"
QUOTES_JS_URL = "https://quotes.toscrape.com/js/"

# Nomes dos arquivos gerados em ``DATA_DIR``.
BOOKS_CSV = "books.csv"
BOOKS_JSON = "books.json"
QUOTES_CSV = "quotes.csv"
QUOTES_JSON = "quotes.json"
QUOTES_JS_CSV = "quotes_js.csv"
QUOTES_JS_JSON = "quotes_js.json"

# Parâmetros de "boa vizinhança" para não sobrecarregar os servidores.
USER_AGENT = "WebScrapingPipeline/1.0 (projeto de portfolio para fins educacionais)"
REQUEST_TIMEOUT = 15  # segundos
REQUEST_DELAY = 0.3  # segundos entre requisições sequenciais
