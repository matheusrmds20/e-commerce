import logging
import ssl
from contextlib import asynccontextmanager

from celery import Celery
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.api.exceptions import register_exception_handlers
from app.api.limiter import limiter
from app.api.router import router
from app.core.config import get_settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.security import motivo_secret_key_insegura

logger = logging.getLogger(__name__)

settings = get_settings()


def _log_configuracao_rede() -> None:
    """Imprime os hosts e origens efetivos no boot.

    No plano free do Render não há Shell, então o log de startup é a única
    janela para conferir o que o processo realmente carregou.

    Isso resolve um diagnóstico enganoso: `TrustedHostMiddleware` e
    `CORSMiddleware` rejeitam com 400 / sem header CORS antes de chegar no
    handler, então **nada aparece no log da aplicação** — o sintoma vira
    "a API está fora" quando na verdade é host/origem fora da allowlist.
    """
    hosts = list(settings.ALLOWED_HOSTS)
    origens = list(settings.CORS_ORIGINS)

    logger.info("config de rede efetiva | DEBUG=%s", settings.DEBUG)
    logger.info("ALLOWED_HOSTS (%d): %s", len(hosts), ", ".join(hosts))
    logger.info("CORS_ORIGINS (%d): %s", len(origens), ", ".join(origens))

    # Dicas de produção: só alerta (não derruba). O RuntimeError do lifespan
    # continua sendo o guard duro para SECRET_KEY e CORS com '*'.
    if not settings.DEBUG:
        hosts_locais = {"localhost", "127.0.0.1", "testserver"}
        origens_locais = {
            o for o in origens if "localhost" in o or "127.0.0.1" in o
        }

        if all(h in hosts_locais for h in hosts):
            logger.warning(
                "ALLOWED_HOSTS contém apenas hosts locais. Em produção o "
                "TrustedHostMiddleware responde 400 para o domínio público. "
                'Defina no painel, em JSON: ALLOWED_HOSTS=["sua-api.onrender.com"]'
            )

        if origens_locais and len(origens_locais) == len(origens):
            logger.warning(
                "CORS_ORIGINS contém apenas origens locais. O front em produção "
                "será bloqueado pelo navegador (No 'Access-Control-Allow-Origin'). "
                'Defina no painel, em JSON: CORS_ORIGINS=["https://seu-front.vercel.app"]'
            )

        if any(h in hosts_locais for h in hosts):
            logger.warning(
                "ALLOWED_HOSTS inclui host local (%s) com DEBUG=false. "
                "Não quebra nada, mas amplia a superfície sem necessidade.",
                ", ".join(sorted(h for h in hosts if h in hosts_locais)),
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.DEBUG:
        # Entropia, não comprimento: com HS256 a SECRET_KEY assina E verifica
        # os JWT, então uma chave longa porém previsível ("a"*64) permitiria
        # forjar tokens de admin sem senha. Ver app/core/security.py.
        motivo = motivo_secret_key_insegura(settings.SECRET_KEY)
        if motivo:
            raise RuntimeError(
                f"SECRET_KEY insegura para produção: {motivo}\n"
                'Gere uma nova com: python -c "import secrets; '
                'print(secrets.token_urlsafe(32))"'
            )
        if "*" in settings.CORS_ORIGINS:
            raise RuntimeError("CORS_ORIGINS não pode conter '*' em produção.")
    _log_configuracao_rede()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)
app.state.limiter = limiter

register_exception_handlers(app)
app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=settings.DEBUG)
def read_root():
    if settings.DEBUG:
        return {"message": "Hello World"}
    return Response(status_code=204)


celery = Celery(
    "ecommerce",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery.conf.imports = ("app.utils.email", "app.utils.receipt_tasks")
celery.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

if settings.FORCE_HTTPS:
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
    expose_headers=["Retry-After"],
    max_age=600,
)
