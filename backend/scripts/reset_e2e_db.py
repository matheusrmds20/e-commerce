"""Recria o banco de testes E2E do zero (schema + migrations + seed).

Motivação: o banco local ``bookcommerce-e2e`` PERSISTE entre execuções e
acumula estado (pedidos, baixas de estoque, reviews...). Isso deixa produtos
"Esgotados" e quebra os specs E2E em execuções posteriores. No CI o banco já
nasce limpo (service postgres do GitHub Actions), então este script replica o
mesmo comportamento para o ambiente local.

Uso (da raiz do repo):
    DATABASE_URL="postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/bookcommerce-e2e" \\
        venv/Scripts/python backend/scripts/reset_e2e_db.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

if not (os.environ.get("E2E_DATABASE_URL") or os.environ.get("DATABASE_URL")) and load_dotenv:
    load_dotenv(BACKEND_DIR / ".env", override=False)

E2E_DATABASE_URL = os.environ.get("E2E_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not E2E_DATABASE_URL:
    raise SystemExit(
        "Defina E2E_DATABASE_URL (ou DATABASE_URL) apontando para o banco de teste E2E!\n"
        'Ex.: export E2E_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5433/bookcommerce-e2e"'
    )


def _drop_and_create() -> None:
    """Deruba e recria o database alvo (terminando conexões abertas)."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    url = make_url(E2E_DATABASE_URL)
    dbname = url.database
    conn = psycopg2.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    quoted = f'"{dbname}"'
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = %s AND pid <> pg_backend_pid()",
        (dbname,),
    )
    cur.execute(f"DROP DATABASE IF EXISTS {quoted}")
    cur.execute(f'CREATE DATABASE {quoted} OWNER {url.username or "postgres"}')
    cur.close()
    conn.close()
    print(f"[reset-e2e] banco '{dbname}' recriado do zero.")


def _migrate_and_seed() -> None:
    """Aplica migrations até a head e popula o banco (categorias + produtos)."""
    env = dict(os.environ, DATABASE_URL=E2E_DATABASE_URL)
    alembic = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    print_alembic_output(alembic)

    seed = subprocess.run(
        [sys.executable, "-m", "scripts.seed"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    print(seed.stdout or seed.stderr)
    if seed.returncode != 0:
        raise SystemExit(f"[reset-e2e] seed falhou:\n{seed.stderr}")


def print_alembic_output(proc) -> None:
    if proc.returncode != 0:
        raise SystemExit(f"[reset-e2e] migrations falharam:\n{proc.stderr}")
    for line in proc.stdout.splitlines():
        if "Running upgrade" in line or "Context impl" in line:
            print(line)


if __name__ == "__main__":
    _drop_and_create()
    _migrate_and_seed()
    print("[reset-e2e] pronto: schema na head + 4 categorias + 24 produtos.")
