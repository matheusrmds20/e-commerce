"""Alembic environment configuration.

Carrega as settings da aplicação para obter a URL do banco de dados
e importa os models para autodetect das migrations.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from backend.app.db.database import Base

# Importa os models para registro no metadata
# noqa: F401 - necessário para o autogenerate detectar as tabelas
# Os demais models serão adicionados conforme implementados nas próximas fases
from app.models import User  # noqa: F401

# Alembic Config object
config = context.config

# Seta a URL do banco a partir das settings da aplicação
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configura logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata dos models para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Roda migrations no modo offline (gera SQL sem conectar no banco)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Roda migrations no modo online (conecta no banco)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()