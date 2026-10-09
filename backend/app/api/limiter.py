"""Rate limiting da API (slowapi).

Cria a instância global do ``Limiter`` usada pelos decorators
``@limiter.limit(...)`` nas rotas sensíveis e pelo limite padrão
(``RATE_LIMIT_DEFAULT``) aplicado a todas as rotas sem limite explícito.

Quando ``RATE_LIMIT_ENABLED=false`` (ex.: suíte de testes), a instância é
criada com ``enabled=False`` e os decorators viram no-ops — o código das
rotas não precisa mudar.

O writup no app (obrigatório para o slowapi funcionar com FastAPI) fica em
``app.main``: ``app.state.limiter = limiter`` e o handler de 429 é registrado
via ``register_exception_handlers`` (app/api/exceptions.py).
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

_settings = get_settings()


def _client_key(request: Request) -> str:
    """Identificador do cliente para o rate limit (IP real).

    Em produção o app roda atrás de um reverse proxy (nginx/Caddy), então
    ``request.client.host`` seria sempre o IP do proxy — todos os usuários
    cairiam no mesmo bucket. Com ``RATE_LIMIT_TRUST_XFF=true`` (default),
    usa-se o primeiro IP do header ``X-Forwarded-For`` (o mais próximo do
    cliente). Se o Uvicorn for exposto à internet SEM proxy, configure o flag
    como ``false`` para evitar bypass via header forjado.
    """
    if _settings.RATE_LIMIT_TRUST_XFF:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_key,
    default_limits=[_settings.RATE_LIMIT_DEFAULT],
    storage_uri=_settings.RATE_LIMIT_STORAGE_URI,
    enabled=_settings.RATE_LIMIT_ENABLED,
    headers_enabled=_settings.RATE_LIMIT_HEADERS_ENABLED,
)
