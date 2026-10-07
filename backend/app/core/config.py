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
