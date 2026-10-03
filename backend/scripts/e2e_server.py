"""Sobe a API FastAPI apontando para o banco de TESTE E2E.

Uso (de qualquer cwd do repo):
    venv/Scripts/python.exe backend/scripts/e2e_server.py
    venv/Scripts/python.exe backend/scripts/e2e_server.py --port 8000

Por que este wrapper existe:
- O app usa app.core.config.get_settings() com @lru_cache e lê DATABASE_URL
  uma única vez. Para o E2E precisamos apontar para o banco isolado
  `bookcommerce-e2e` ANTES do primeiro import de app.* (senão o .env do
  backend, que aponta para o banco de dev, vence).
- O restante das settings (secrets do Mercado Pago, FRONTEND_URL, etc.) vem
  do .env do backend, carregado por caminho absoluto (ENV_FILE em
  app/core/config.py), então não depende do diretório de execução.
"""
import os
import sys
from pathlib import Path

# Garante que a raiz do backend/ esteja no sys.path, já que este script roda
# como `python backend/scripts/e2e_server.py` (sys.path[0] = backend/scripts).
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# MUST ser setado antes do primeiro import de app.*.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg2://postgres:postgres@localhost:5433/bookcommerce-e2e"
)

import uvicorn  # noqa: E402


def main() -> None:
    # Porta sobrescrevível via `--port N` (default 8000, igual à API de dev).
    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()