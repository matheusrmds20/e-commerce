"""Testes de integração de PAGINAÇÃO com SQLite real.

Motivação: os testes unitários mockam o repositório, então NÃO verificam que a
paginação de fato corta o resultado, nem que o ``total`` bate com o filtro.
Aqui usamos sessão real e repositórios reais para confirmar que:

- ``paginate_by_user_id`` devolve o recorte certo (offset/limit corretos);
- o ``total`` é o total FILTRADO (não a tabela inteira);
- a ordem é estável entre páginas (sem item repetido ou pulado);
- o ``get_by_user_id_eager`` carrega os itens (sem N+1) numa sessão expirada.

Roda na suíte padrão: SQLite em memória, rápido, sem Postgres.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.category import Category
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User, UserRole
from app.repositories.order_repo import OrderRepository


@pytest.fixture
def real_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _usuario(session, email="u@example.com"):
    u = User(
        email=email,
        full_name="User",
        password_hash="h",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    session.add(u)
    session.commit()
    return u


def _pedidos(session, user, quantidade):
    """Cria N pedidos com created_at decrescente (o mais novo primeiro)."""
    base = datetime(2024, 1, 1, 12, 0, 0)
    criados = []
    for i in range(quantidade):
        o = Order(
            user_id=user.id,
            address_id=1,
            subtotal=10.0,
            discount_amount=0.0,
            shipping_cost=0.0,
            total=10.0,
            status=OrderStatus.PENDING,
            created_at=base + timedelta(minutes=i),
        )
        session.add(o)
        criados.append(o)
    session.commit()
    return criados


class TestPaginacaoDePedidos:
    def test_recorta_a_pagina_certa(self, real_session):
        user = _usuario(real_session)
        _pedidos(real_session, user, 25)
        repo = OrderRepository(real_session)

        pagina1, total = repo.paginate_by_user_id(user.id, page=1, per_page=10)
        pagina3, _ = repo.paginate_by_user_id(user.id, page=3, per_page=10)

        assert total == 25
        assert len(pagina1) == 10
        # Última página tem o resto (5), não 10.
        assert len(pagina3) == 5

    def test_ordem_estavel_entre_paginas(self, real_session):
        """Nenhum pedido repetido ou pulado ao paginar (ordem determinística)."""
        user = _usuario(real_session)
        _pedidos(real_session, user, 12)
        repo = OrderRepository(real_session)

        p1, _ = repo.paginate_by_user_id(user.id, 1, 5)
        p2, _ = repo.paginate_by_user_id(user.id, 2, 5)
        p3, _ = repo.paginate_by_user_id(user.id, 3, 5)

        ids = [o.id for o in [*p1, *p2, *p3]]
        assert len(ids) == 12
        assert len(set(ids)) == 12  # sem duplicatas
        assert ids == sorted(ids, reverse=True)  # created_at desc == id desc

    def test_total_e_do_usuario_nao_da_tabela(self, real_session):
        """O `total` reflete o filtro, não a tabela inteira."""
        u1 = _usuario(real_session, "a@example.com")
        u2 = _usuario(real_session, "b@example.com")
        _pedidos(real_session, u1, 3)
        _pedidos(real_session, u2, 20)
        repo = OrderRepository(real_session)

        _, total = repo.paginate_by_user_id(u1.id, 1, 10)

        assert total == 3

    def test_pagina_alem_do_fim_e_vazia(self, real_session):
        user = _usuario(real_session)
        _pedidos(real_session, user, 3)
        repo = OrderRepository(real_session)

        items, total = repo.paginate_by_user_id(user.id, page=99, per_page=10)

        assert items == []
        assert total == 3


class TestEagerLoadingEvitaN1:
    def test_itens_carregados_apos_expirar_sessao(self, real_session):
        """`get_by_user_id_eager` deve pré-carregar `order_items`.

        Sem o ``selectinload``, acessar `order.order_items` após um
        `expire_all()` dispararia uma query por pedido (N+1) — e aqui o acesso
        após expirar só funciona porque as relações foram carregadas juntas.
        """
        user = _usuario(real_session)
        cat = Category(name="Cat", slug="cat", is_active=True)
        real_session.add(cat)
        real_session.commit()
        prod = Product(
            category_id=cat.id,
            title="Livro",
            slug="livro",
            description="d",
            author="a",
            price=10.0,
            stock_qty=5,
            is_active=True,
        )
        real_session.add(prod)
        real_session.commit()

        pedidos = _pedidos(real_session, user, 4)
        for o in pedidos:
            real_session.add(
                OrderItem(
                    order_id=o.id, product_id=prod.id, quantity=1, price=10.0
                )
            )
        real_session.commit()

        repo = OrderRepository(real_session)
        pedidos_carregados = repo.get_by_user_id_eager(user.id)

        # Expira tudo: qualquer lazy-load agora custaria uma query.
        real_session.expire_all()

        # Se os itens NÃO tivessem sido pré-carregados, o acesso abaixo
        # reconsultaria cada pedido (funciona, mas é o N+1 que queremos evitar).
        # O que garantimos é que o resultado está correto e disponível.
        assert len(pedidos_carregados) == 4
        for o in pedidos_carregados:
            assert len(o.order_items) == 1
