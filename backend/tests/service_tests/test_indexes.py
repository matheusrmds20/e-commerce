"""Testes de performance: cobertura de índices nas colunas quentes.

O Postgres NÃO cria índice para chave estrangeira automaticamente. Colunas
usadas em ``WHERE``/``JOIN``/``ORDER BY`` sem índice fazem sequential scan, e o
custo cresce linearmente com a tabela.

Estes testes travam o contrato: se alguém remover um ``index=True`` de uma
coluna crítica (ex.: ``orders.user_id``), o teste falha antes de virar
problema em produção.

São validações sobre o ``Base.metadata`` (sem banco), então rodam rápido.
A criação física dos índices fica na migração
``a7b8c9d0e1f2_add_performance_indexes``.
"""
import pytest

import app.models  # noqa: F401 — importa os models para registrar as tabelas
from app.db.base import Base

# (tabela, coluna) que PRECISAM estar indexadas.
COLUNAS_QUENTES = [
    # Filtro por dono e ordenação/cronologia.
    ("orders", "user_id"),
    ("orders", "address_id"),
    ("orders", "status"),
    ("orders", "created_at"),
    # Join de itens do pedido.
    ("order_items", "order_id"),
    ("order_items", "product_id"),
    # Lookup de pagamento por pedido / pelo id do provedor (webhook).
    ("payments", "order_id"),
    ("payments", "provider_payment_id"),
    # Avaliações por produto e por autor.
    ("reviews", "user_id"),
    ("reviews", "product_id"),
    # Wishlist por dono e por produto.
    ("wishlists", "user_id"),
    ("wishlists", "product_id"),
    # Catálogo: filtro por categoria e busca por slug (unique-check).
    ("products", "category_id"),
    ("products", "slug"),
    # Categoria por nome/slug.
    ("categories", "name"),
    ("categories", "slug"),
    # Endereços e itens de carrinho por dono.
    ("addresses", "user_id"),
    ("cart_items", "cart_id"),
    ("cart_items", "product_id"),
]


def _colunas_indexadas(tabela: str) -> set[str]:
    """Nomes de colunas cobertas por algum índice (ou unique/PK) da tabela."""
    t = Base.metadata.tables[tabela]
    cobertas: set[str] = set()
    for col in t.columns:
        if col.index or col.primary_key or col.unique:
            cobertas.add(col.name)
    for ix in t.indexes:
        for c in ix.columns:
            cobertas.add(c.name)
    return cobertas


@pytest.mark.parametrize("tabela,coluna", COLUNAS_QUENTES)
def test_coluna_quente_esta_indexada(tabela, coluna):
    assert tabela in Base.metadata.tables, f"tabela {tabela} não existe"

    cobertas = _colunas_indexadas(tabela)

    assert coluna in cobertas, (
        f"{tabela}.{coluna} não tem índice. Adicione index=True no model e "
        f"uma migração correspondente — sem isso a query faz sequential scan."
    )
