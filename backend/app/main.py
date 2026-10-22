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

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.DEBUG:
        if settings.SECRET_KEY.startswith("change-me") or len(settings.SECRET_KEY) < 32:
            raise RuntimeError("SECRET_KEY insegura para produção (fora do default e min. 32 chars).")
        if "*" in settings.CORS_ORIGINS:
            raise RuntimeError("CORS_ORIGINS não pode conter '*' em produção.")
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
