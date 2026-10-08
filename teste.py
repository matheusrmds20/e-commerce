"""Cliente OAuth2 de teste para o Melhor Envio.

Fluxo de autenticação da API (https://docs.melhorenvio.com.br/reference):

  1. ``authorize``  -> gera a URL que deve ser aberta no navegador. O lojista
                       autoriza a aplicação e o Melhor Envio redireciona para a
                       ``redirect_uri`` (callback) com o parâmetro ``code``.
  2. ``token``      -> troca o ``code`` por ``access_token`` + ``refresh_token``
                       (grant_type=authorization_code).
  3. ``refresh``    -> renova o ``access_token`` já expirado (grant_type=
                       refresh_token) usando o ``refresh_token`` salvo.

Uso (linha de comando):

    # 1. Imprime a URL de autorização para abrir no navegador:
    python teste.py authorize

    # 2. Troca o code retornado (na URL de callback) pelo token:
    python teste.py token --code SEU_CODE

    # 3. Renova o access_token a partir de um refresh_token:
    python teste.py refresh --refresh-token SEU_REFRESH_TOKEN

Configuração via variáveis de ambiente (recomendado, para não deixar segredo
no código), OU via flags no próprio comando:

    MELHOR_ENVIO_CLIENT_ID
    MELHOR_ENVIO_CLIENT_SECRET
    MELHOR_ENVIO_REDIRECT_URI
    MELHOR_ENVIO_SANDBOX   (true/false, default true)
    MELHOR_ENVIO_SCOPE     (scopes separados por espaço, opcional)

Observações:
  - Em sandbox use o endpoint https://sandbox.melhorenvio.com.br e o app
    cadastrado em https://sandbox.melhorenvio.com.br/painel/integracoes/area-dev.
  - A ``redirect_uri`` deve ser EXATAMENTE igual à cadastrada no app.
  - Para cotação de frete, inclua o scope ``shipping-calculate``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE_PRODUCTION = "https://melhorenvio.com.br"
BASE_SANDBOX = "https://sandbox.melhorenvio.com.br"

# Caminho padrão do arquivo .env do backend (o mesmo usado pela aplicação em
# app/core/config.py). O script só o usa quando a chave não existir como
# variável de ambiente/fl ag de linha de comando.
ENV_FILE = Path(__file__).resolve().parent / "backend" / ".env"


# ---------------------------------------------------------------------------
# Leitor simples de .env (formato CHAVE=valor)
# ---------------------------------------------------------------------------


def _parse_env_file(path: Path) -> dict[str, str]:
    """Lê um arquivo .env simples (linhas `CHAVE=valor`)."""
    dados: dict[str, str] = {}
    if not path.exists():
        return dados

    for linha in path.read_text(encoding="utf-8").splitlines():
        # ignora linhas em branco e comentários
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip()
        # remove aspas simples/duplas que envolvam o valor
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ('"', "'"):
            valor = valor[1:-1]
        dados[chave] = valor
    return dados


# Cache leve do conteúdo do .env (evita reler a cada chamada).
_env_cache: dict[str, str] | None = None


def get_env(name: str, default: str | None = None) -> str | None:
    """Lê uma variável de ambiente; se ausente, cai no backend/.env.

    Prioridade: variável de ambiente do processo > arquivo .env do backend.
    (Flags de CLI têm prioridade maior e são tratadas fora, no ``load_config``.)
    """
    global _env_cache
    val = os.getenv(name)
    if val is not None:
        return val
    if _env_cache is None:
        _env_cache = _parse_env_file(ENV_FILE)
    return _env_cache.get(name, default)


# ---------------------------------------------------------------------------
# Helpers de configuração
# ---------------------------------------------------------------------------


def env_bool(name: str, default: bool = False) -> bool:
    val = get_env(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

# Scopes mínimos para o fluxo de frete (cotação + visualização de empresas).
DEFAULT_SCOPE = "shipping-calculate companies-read"


def base_url() -> str:
    return BASE_SANDBOX if env_bool("MELHOR_ENVIO_SANDBOX", True) else BASE_PRODUCTION


def load_config(args) -> dict:
    """Une flags de linha de comando, variáveis de ambiente e o .env do backend.

    Prioridade (da maior para a menor):
      1. flag passada no comando (ex.: --client-secret)
      2. variável de ambiente do shell (ex.: MELHOR_ENVIO_CLIENT_SECRET)
      3. arquivo backend/.env (fallback final)
    """
    # Nem todo subparser define todas as flags; use getattr com default None.
    def flag(nome: str) -> str | None:
        return getattr(args, nome, None)

    def resolver(nome_env: str) -> str | None:
        # flag  > variável de ambiente do processo  > .env do backend
        valor = flag(nome_env.removeprefix("MELHOR_ENVIO_").lower())
        if valor:
            return valor
        return get_env(nome_env)

    cfg = {
        "client_id": resolver("MELHOR_ENVIO_CLIENT_ID"),
        "client_secret": resolver("MELHOR_ENVIO_CLIENT_SECRET"),
        "redirect_uri": resolver("MELHOR_ENVIO_REDIRECT_URI"),
        "scope": resolver("MELHOR_ENVIO_SCOPE") or DEFAULT_SCOPE,
    }
    # A URL base é determinada pela variável de ambiente/.env, não por flag,
    # para evitar misturar sandbox com produção acidentalmente.
    return cfg


def require(cfg: dict, key: str, label: str):
    if not cfg.get(key):
        print(
            f"ERRO: {label} ausente. "
            f"Defina via variável de ambiente (MELHOR_ENVIO_{key.upper()}) "
            f"ou flag --{key.replace('_', '-')}.",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def cmd_authorize(cfg: dict) -> None:
    require(cfg, "client_id", "client_id")
    require(cfg, "redirect_uri", "redirect_uri")

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "state": "teste",
        "scope": cfg["scope"],
    }
    url = f"{base_url()}/oauth/authorize?{urlencode(params, quote_via=lambda s, *a: s)}"

    print("Abra a URL abaixo no navegador e autorize o acesso:")
    print(url)
    print("\nApós autorizar, o navegador redirecionará para a seu callback com")
    print("um parâmetro ?code=SEU_CODE. Copie esse valor e rode:")
    print("  python teste.py token --code SEU_CODE")


def _token_request(
    base: str,
    payload: dict,
    client_id: str,
    client_secret: str,
) -> dict:
    body = {
        "client_id": client_id,
        "client_secret": client_secret,
        **payload,
    }
    resp = requests.post(
        f"{base}/oauth/token",
        json=body,
        headers={"Accept": "application/json", "User-Agent": "bookcommerce-test"},
        timeout=20,
    )
    if resp.status_code not in range(200, 300):
        print(f"ERRO HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def cmd_token(cfg: dict, code: str) -> None:
    require(cfg, "client_id", "client_id")
    require(cfg, "client_secret", "client_secret")
    require(cfg, "redirect_uri", "redirect_uri")
    if not code:
        print("Forneça o parâmetro --code (código retornado no callback).", file=sys.stderr)
        sys.exit(2)

    data = _token_request(
        base_url(),
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg["redirect_uri"],
        },
        cfg["client_id"],
        cfg["client_secret"],
    )
    _print_tokens(data)


def cmd_refresh(cfg: dict, refresh_token: str) -> None:
    require(cfg, "client_id", "client_id")
    require(cfg, "client_secret", "client_secret")
    if not refresh_token:
        print(
            "Forneça o parâmetro --refresh-token (obtido na resposta do token).",
            file=sys.stderr,
        )
        sys.exit(2)

    data = _token_request(
        base_url(),
        {"grant_type": "refresh_token", "refresh_token": refresh_token},
        cfg["client_id"],
        cfg["client_secret"],
    )
    _print_tokens(data)


def _print_tokens(data: dict) -> None:
    print("\n--- Tokens recebidos ---")
    print(f"token_type     : {data.get('token_type')}")
    print(f"expires_in     : {data.get('expires_in')} s")
    print(f"access_token   : {data.get('access_token')}")
    print(f"refresh_token  : {data.get('refresh_token')}")
    print("\nCopie o access_token para a variável MELHOR_ENVIO_API_TOKEN do seu")
    print("backend/.env para habilitar a cotação de frete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    # Flags comuns (fungíveis com variáveis de ambiente).
    u = sub.add_parser("authorize", help="Gera a URL de autorização para o navegador.")
    u.add_argument("--client-id")
    u.add_argument("--redirect-uri")
    u.add_argument("--scope")

    t = sub.add_parser("token", help="Troca o code por access_token.")
    t.add_argument("--code", required=False)
    t.add_argument("--client-id")
    t.add_argument("--client-secret")
    t.add_argument("--redirect-uri")

    r = sub.add_parser("refresh", help="Renova o access_token.")
    r.add_argument("--refresh-token", required=False)
    r.add_argument("--client-id")
    r.add_argument("--client-secret")

    args = parser.parse_args()
    cfg = load_config(args)

    if args.comando == "authorize":
        cmd_authorize(cfg)
    elif args.comando == "token":
        cmd_token(cfg, getattr(args, "code", None))
    elif args.comando == "refresh":
        cmd_refresh(cfg, getattr(args, "refresh_token", None))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()