from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# pool_pre_ping evita usar conexões quebradas (morta do Postgres) e um pool
# maior cobre os picos dos specs E2E em paralelo (o default 5+10 saturava com
# o traffic dos testes, gerando QueuePool.TimeoutError em cascata).
#
# Esses parâmetros NÃO se aplicam ao SQLite: seus pools (SingletonThreadPool /
# StaticPool) não aceitam `pool_size`/`max_overflow`. Por isso só passamos o
# pool tunado para bancos que usam pool de servidor (ex.: Postgres em dev/prod).
url = make_url(settings.DATABASE_URL)
engine_kwargs: dict = {"echo": settings.DEBUG}
if url.get_backend_name() != "sqlite":
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
        }
    )

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
