"""Testes de integração de CONCORRÊNCIA do carrinho (Postgres real).

Ao contrário da suíte unitária (que usa ``MagicMock``/sqlite), estes testes
apontam para um banco PostgreSQL dedicado e disparam threads com sessões
independentes — ou seja, exercitam de verdade locks de linha (``FOR UPDATE``),
transações (``with session.begin()``) e a constraint única
``cart_items(cart_id, product_id)`` sob contenção.

Como rodar (com o Postgres de dev de pé). As credenciais vêm do ambiente — este
teste **não** guarda usuário/senha no código:

    CONC_DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce_conc" \\
        pytest backend/tests/integration_tests/test_cart_concurrency.py -v

Pré-requisito único: o banco ```bookcommerce_conc`` criado e com a schema no head:

    psql -c "CREATE DATABASE bookcommerce_conc"
    CONC_DATABASE_URL="postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce_conc" \\
        alembic upgrade head

O teste é marcado com ``pytest.mark.integration`` justamente para ficar fora da
suíte padrão (que roda com sqlite/:memory: e não suporta ``FOR UPDATE`` real).
"""
import os
import threading

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.cart import Cart
from app.models.category import Category
from app.models.product import Product
from app.models.user import User, UserRole
from app.services.cart_service import CartService

# Aponta para o banco de concorrência (deve existir e estar com schema no head).
# Sem credenciais no código: defina CONC_DATABASE_URL no ambiente.
TEST_DATABASE_URL = os.environ.get("CONC_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip(
        "Defina CONC_DATABASE_URL apontando para o Postgres de concorrência "
        "(ex.: postgresql+psycopg2://<user>:<password>@localhost:5433/bookcommerce_conc).",
        allow_module_level=True,
    )

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def conc_postgres():
    """/Cria o engine/sessionmaker ligado ao Postgres de teste."""
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield Session
    engine.dispose()


def _limpar(Session):
    """Remove dados de carrinhos/produtos/categorias/usuários criados pelo teste."""
    with Session() as s:
        s.execute(text("DELETE FROM cart_items"))
        s.execute(text("DELETE FROM carts"))
        s.execute(text("DELETE FROM products"))
        s.execute(text("DELETE FROM categories"))
        s.execute(text("DELETE FROM users"))
        s.commit()


def _criar_monte(Session):
    """Seeda categoria + produto com estoque alto + usuário + carrinho."""
    with Session() as s:
        cat = Category(name="Conc Test", slug="conc-test", is_active=True)
        s.add(cat)
        s.flush()

        # Produto com estoque folgado para não interferir na contagem.
        prod = Product(
            category_id=cat.id,
            title="Livro Concorrencia",
            slug="livro-concorrencia",
            description="para testes de concorrencia",
            author="Autor Teste",
            price=30.0,
            stock_qty=1000,
            is_active=True,
        )
        s.add(prod)
        s.flush()

        user = User(
            email="conc@test.com",
            password_hash="x",
            full_name="Conc Test",
            role=UserRole.CUSTOMER,
            is_active=True,
        )
        s.add(user)
        s.flush()

        cart = Cart(user_id=user.id)
        s.add(cart)
        s.flush()

        s.commit()
        return {"product_id": prod.id, "user_id": user.id, "cart_id": cart.id}


class TestAddItemConcorrente:
    """Duplicação sob a constraint única: N add_item do MESMO produto.

    Requisito do produto: SOMENTE 1 linha por (cart_id, product_id) e a
    quantidade final = soma de todas as adições, sem nenhum IntegrityError
    escapando para o chamador (o retry do service absorve a race).
    """

    def test_adds_simultaneos_produzem_uma_linha(self, conc_postgres):
        Session = conc_postgres
        _limpar(Session)
        dados = _criar_monte(Session)
        product_id = dados["product_id"]
        cart_id = dados["cart_id"]
        user_id = dados["user_id"]

        N = 8  # threads — todas tentam adicionar 1 unidade do MESMO produto
        item_esperado = 1  # uma linha só
        qtd_esperada = N  # 1 (linha) + somas

        erros = []

        def adicionar():
            try:
                with Session() as s:
                    svc = CartService(s)
                    # Uso SEM exclusão: o mesmo (cart, product) a partir de
                    # estados iniciais distintos exercita a constraint única.
                    svc.add_item(cart_id, user_id, product_id, 1)
            except Exception as exc:  # pragma: no cover
                erros.append(exc)

        threads = [threading.Thread(target=adicionar) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not erros, f"add_item estourou exceção: {erros}"

        # Estado final: 1 linha com quantidade = N (nenhuma perda de update).
        with Session() as s:
            linhas = s.execute(
                text(
                    "SELECT quantity FROM cart_items "
                    "WHERE cart_id=:c AND product_id=:p"
                ),
                {"c": cart_id, "p": product_id},
            ).fetchall()
        assert len(linhas) == item_esperado, (
            f"Esperava {item_esperado} linha, achei {len(linhas)}. "
            "A constraint única NÃO impediu a duplicação."
        )
        assert linhas[0][0] == qtd_esperada, (
            f"Esperava quantidade {qtd_esperada}, achei {linhas[0][0]}. "
            "Houve perda de update na soma concorrente."
        )

        _limpar(Session)


class TestAddRemoveRace:
    """Perda de update entre add_item e remove_item (concorrente).

    Cenário apontado na análise: `add_item` (computa quantidade_total sobre a
    leitura atual) concorrendo com `remove_item` (some com a linha). O objetivo
    é garantir que o sistema não baixa para um estado silenciosamente
    inconsistente (ex.: remover durante um add somando em cima de linha deletada
    sem a constraint rejeitar).
    """

    def test_add_vs_remove_nao_deixa_estado_quebrado(self, conc_postgres):
        Session = conc_postgres
        _limpar(Session)
        dados = _criar_monte(Session)
        product_id = dados["product_id"]
        cart_id = dados["cart_id"]
        user_id = dados["user_id"]

        # Primeiro adiciona 1 unidade, depois dispara add(+1) x remove em loop.
        # Como remove e add disputam a mesma linha, espera-se estado consistente
        # no final: 0 ou 1 linha, quantidade <= 2, NUNCA a linha somada sobre
        # outra já removida deixando 2 linhas (constraint) nem loop infinito.
        with Session() as s:
            CartService(s).add_item(cart_id, user_id, product_id, 1)

        RODADAS = 6
        erros = []

        # Cada worker usa sessão própria (concorrência real).
        def add_worker():
            try:
                with Session() as s:
                    CartService(s).add_item(cart_id, user_id, product_id, 1)
            except Exception as exc:  # pragma: no cover
                erros.append(exc)

        def remove_worker():
            try:
                # Sessão 1: só para achar o id da linha (query separada).
                # Não podemos fazer query e depois passar a MESMA sessão ao
                # service, pois `with self.session.begin()` falha se já há
                # transação iniciada nesta sessão.
                with Session() as s1:
                    item_id = s1.execute(
                        text(
                            "SELECT id FROM cart_items "
                            "WHERE cart_id=:c AND product_id=:p LIMIT 1"
                        ),
                        {"c": cart_id, "p": product_id},
                    ).scalar()
                if item_id is not None:
                    with Session() as s2:  # sessão própria para o service
                        CartService(s2).remove_item(cart_id, user_id, item_id)
            except Exception as exc:  # pragma: no cover
                erros.append(exc)

        import time

        for _ in range(RODADAS):
            ta = threading.Thread(target=add_worker)
            tr = threading.Thread(target=remove_worker)
            ta.start()
            tr.start()
            ta.join()
            tr.join()
            time.sleep(0.01)

        assert not erros, f"exceção durante race: {erros}"

        # Estado jamais pode ter 2 linhas para o mesmo (cart, product).
        with Session() as s:
            total_linhas = s.execute(
                text(
                    "SELECT COUNT(*) FROM cart_items "
                    "WHERE cart_id=:c AND product_id=:p"
                ),
                {"c": cart_id, "p": product_id},
            ).scalar()
            qtd = s.execute(
                text(
                    "SELECT COALESCE(SUM(quantity),0) FROM cart_items "
                    "WHERE cart_id=:c AND product_id=:p"
                ),
                {"c": cart_id, "p": product_id},
            ).scalar()
        assert total_linhas <= 1, (
            f"constraint violada: {total_linhas} linhas para o mesmo item"
        )
        # O máximo possível dado o padrão add(+1) x remove intercalado.
        # (1 inicial + adições) − remoções >= 0. Não pode ser negativo.
        assert qtd >= 0, f"quantidade negativa? {qtd}"

        _limpar(Session)
