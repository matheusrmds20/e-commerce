"""Ambiente de migrations do Alembic.

Este é o env.py ATIVO (apontado por `alembic.ini` → `script_location = alembic`).

Ele faz três coisas que o template padrão não faz:

1. **Carrega a URL do banco das settings da aplicação** (`.env`), em vez do
   placeholder `driver://user:pass@localhost/dbname` do alembic.ini. Sem isso o
   SQLAlchemy tenta carregar um dialeto chamado literalmente "driver" e quebra
   com `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:driver`.

2. **Importa todos os models** para que fiquem registrados em `Base.metadata`.
   Sem esses imports o `--autogenerate` não enxerga as tabelas e gera uma
   migration vazia.

3. **Define `target_metadata = Base.metadata`**, o que dá ao autogenerate o
   "schema desejado" para comparar com o banco real.

Nota sobre imports: o `prepend_sys_path = backend` do alembic.ini coloca a pasta
`backend/` no sys.path, então importamos como `app.*` — que é o mesmo padrão
usado internamente pela aplicação.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Importa as settings da aplicação para obter a URL do banco.
from app.core.config import get_settings
from app.db.base import Base

# Importa TODOS os models para registro no metadata do autogenerate.
# noqa: F401 — os imports são "usados" por efeito colateral (registrar tabelas).
from app.models.address import Address  # noqa: F401
from app.models.cart import Cart  # noqa: F401
from app.models.cart_item import CartItem  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.coupon import Coupon  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.order_item import OrderItem  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_coupon import UserCoupon  # noqa: F401
from app.models.wishlist import Wishlist  # noqa: F401

# Objeto de configuração do Alembic (lê o alembic.ini).
config = context.config

# Seta a URL real do banco a partir das settings (.env).
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configura o logging a partir do arquivo .ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata alvo do autogenerate — agora populado pelos imports acima.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Roda migrations em modo 'offline'.

    Neste modo configuramos o contexto apenas com a URL, sem criar Engine.
    Útil para gerar o SQL sem precisar de um DBAPI disponível.
    """
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
    """Roda migrations em modo 'online' (com conexão real ao banco)."""
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
