from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Caminho absoluto do .env na raiz do backend.
# Usar caminho absoluto (em vez do relativo ".env") evita que o arquivo deixe
# de ser encontrado quando o processo roda de outro diretório — por exemplo
# `alembic` executado da raiz do repositório.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "CRM de vendas"
    DEBUG: bool = False

    FRONTEND_URL: str
    BACKEND_URL: str
    # Origens permitidas pelo CORS. O default cobre os dev servers do Vite
    # (5173) e o preview (4173) — necessários para desenvolvimento local e para
    # a suíte E2E (front em localhost:5173 chamando o backend em localhost:8000)
    # — além dos domínios de produção. Sobrescreva via env em formato JSON, ex.:
    # CORS_ORIGINS=["https://e-commerce.matheuslab.xyz"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "https://e-commerce.matheuslab.xyz",
        "https://api-e-commerce.matheuslab.xyz",
    ]
    MERCADO_PAGO_ACCESS_TOKEN: str
    MERCADO_PAGO_WEBHOOK_SECRET: str
    # Melhor Envio — API de frete.
    MELHOR_ENVIO_API_TOKEN: str = ""
    # CEP de origem (da loja) usado na cotação de frete.
    MELHOR_ENVIO_ORIGIN_ZIP: str = ""
    # True usa https://sandbox.melhorenvio.com.br ; False usa produção.
    MELHOR_ENVIO_SANDBOX: bool = True
    MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA: str = ""
    VALIDATE_WEBHOOK_SIGNATURE: bool = True
    SECRET_KEY: str = Field(default="change-me-to-a-very-long-secret-key", min_length=32)
    ALGORITHM: str = "HS256"
    # TTL do access token (JWT curta validade, enviado via header Bearer).
    # 15 min em produção (7.3 do plano). Ajuste sobrescreve via env/CI.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    # TTL do refresh token (em dias) — usado para "lembrar-me" e renovar a
    # sessão ativa. Rotativo: a cada refresh, um novo refresh token é emitido.
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SMTP_HOST: str
    SMTP_PORT: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    # Rate limiting (slowapi) — proteção básica contra abuso por IP.
    # Desligue via RATE_LIMIT_ENABLED=false em ambientes sem necessidade
    # (ex.: suíte de testes), pois o front E2E faz muitas chamadas.
    RATE_LIMIT_ENABLED: bool = True
    # Limite padrão aplicado a TODAS as rotas sem limite explícito.
    # Rotas sensíveis (auth, newsletter, webhook...) sobrescrevem com limites
    # próprios via @limiter.limit("...").
    RATE_LIMIT_DEFAULT: str = "200/minute"
    # "memory://" é por-processo (adequado para dev). Em produção com vários
    # workers do Uvicorn use o Redis (já é dependência via Celery), ex.:
    # RATE_LIMIT_STORAGE_URI="redis://localhost:6379/2"
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    # Define se os headers X-RateLimit-* são injetados nas respostas. Mantenha
    # False: no slowapi, com headers ligados todo endpoint decorado precisaria
    # declarar um parâmetro `response: Response` (senão vira 500).
    RATE_LIMIT_HEADERS_ENABLED: bool = False
    # Atrás de nginx/Caddy (produção), request.client.host é sempre o IP do
    # proxy — todos os usuários cairiam no mesmo bucket. True usa o primeiro
    # IP do header X-Forwarded-For. Se o Uvicorn for exposto direto à internet
    # SEM proxy, o header forjado permitiria burlar o limite: use False.
    RATE_LIMIT_TRUST_XFF: bool = True
    # Diretório onde os comprovantes PDF dos pedidos são salvos.
    COMPROVANTES_DIR: str = "comprovantes"

    model_config=SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
        )

    DATABASE_URL: str

@lru_cache
def get_settings():
    return Settings()
