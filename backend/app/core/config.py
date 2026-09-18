from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

# Caminho absoluto do .env na raiz do backend.
# Usar caminho absoluto (em vez do relativo ".env") evita que o arquivo deixe
# de ser encontrado quando o processo roda de outro diretório — por exemplo
# `alembic` executado da raiz do repositório.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "CRM de vendas"
    DEBUG: bool = False

    

    SECRET_KEY: str = Field(default="change-me-to-a-very-long-secret-key", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config=SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
        )

    DATABASE_URL: str 

@lru_cache
def get_settings():
    return Settings()