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
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "https://e-commerce.matheuslab.xyz",
        "https://api-e-commerce.matheuslab.xyz",
    ]
    MERCADO_PAGO_ACCESS_TOKEN: str
    MERCADO_PAGO_WEBHOOK_SECRET: str
    MELHOR_ENVIO_API_TOKEN: str = ""
    MELHOR_ENVIO_ORIGIN_ZIP: str = ""
    MELHOR_ENVIO_SANDBOX: bool = True
    MELHOR_ENVIO_TIMEOUT: float = 15.0
    MERCADO_PAGO_TIMEOUT: float = 8.0
    MERCADO_PAGO_WEBHOOK_SECRETS_EXTRA: str = ""
    VALIDATE_WEBHOOK_SIGNATURE: bool = True
    SECRET_KEY: str = Field(default="change-me-to-a-very-long-secret-key", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
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
    RATE_LIMIT_TRUST_XFF: bool = True
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
