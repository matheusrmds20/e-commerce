""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if not (os.environ.get("E2E_DATABASE_URL") or os.environ.get("DATABASE_URL")) and load_dotenv:

    load_dotenv(BACKEND_DIR / ".env", override=False)



E2E_DATABASE_URL = os.environ.get("E2E_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not E2E_DATABASE_URL:
    raise SystemExit(
        "Defina E2E_DATABASE_URL (ou DATABASE_URL) apontando para o banco de teste "
        "E2E! Também confira se o backend/.env contém esta chave e se o python-dotenv \n"
        "está instalado no ambiente (pip install python-dotenv)\n"
        'Ex.: export E2E_DATABASE_URL="postgresql+psycopg2://<user>:<password>'
        '@localhost:5433/bookcommerce-e2e"'
    )
os.environ["DATABASE_URL"] = E2E_DATABASE_URL


os.environ["RATE_LIMIT_ENABLED"] = "false"

import uvicorn  # noqa: E402


def main() -> None:

    port = 8000
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
