from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "E-commerce"
    DEBUG: bool = False

    FRONTEND_URL: str
    BACKEND_URL: str
    CORS_ORIGINS: list[str] = [
        "https://papiro.matheuslab.xyz",
        "https://e-commerce-de-livros-api.onrender.com",
        "https://e-commerce-nine-nu-59.vercel.app",
    ]
    ALLOWED_HOSTS: list[str] = [
        "testserver",
        "localhost",
        "127.0.0.1",
        "e-commerce-de-livros-api.onrender.com",
        "papiro.matheuslab.xyz",
        "e-commerce-nine-nu-59.vercel.app",
    ]
    FORCE_HTTPS: bool = False
    MERCADO_PAGO_ACCESS_TOKEN: str
    MERCADO_PAGO_WEBHOOK_SECRET: str
    MELHOR_ENVIO_API_TOKEN: str = ""
    MELHOR_ENVIO_ORIGIN_ZIP: str = ""
    MELHOR_ENVIO_SANDBOX: bool = True
    MELHOR_ENVIO_TIMEOUT: float = 15.0
    MERCADO_PAGO_TIMEOUT: float = 8.0
    MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA: str = ""
    VALIDATE_WEBHOOK_SIGNATURE: bool = True
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None
    SMTP_HOST: str
    SMTP_PORT: str
    SMTP_USER: str
    SMTP_PASSWORD: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "200/minute"
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_HEADERS_ENABLED: bool = False
    RATE_LIMIT_TRUST_XFF: bool = False
    LOGIN_LOCKOUT_ENABLED: bool = True
    LOGIN_LOCKOUT_MAX_FAILURES: int = 5
    LOGIN_LOCKOUT_TTL_SECONDS: int = 300
    LOGIN_LOCKOUT_BASE_SECONDS: int = 300
    LOGIN_LOCKOUT_MAX_SECONDS: int = 1800
    LOGIN_LOCKOUT_REDIS_URL: str | None = None
    COMPROVANTES_DIR: str = "comprovantes"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "comprovantes"

    model_config=SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
        )

    DATABASE_URL: str

@lru_cache
def get_settings():
    return Settings()
