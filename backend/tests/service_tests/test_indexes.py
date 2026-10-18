
import pytest

from app.db.base import Base

COLUNAS_QUENTES = [

    ("orders", "user_id"),
    ("orders", "address_id"),
    ("orders", "status"),
    ("orders", "created_at"),
    ("order_items", "order_id"),
    ("order_items", "product_id"),
    ("payments", "order_id"),
    ("payments", "provider_payment_id"),
    ("reviews", "user_id"),
    ("reviews", "product_id"),
    ("wishlists", "user_id"),
    ("wishlists", "product_id"),
    ("products", "category_id"),
    ("products", "slug"),
    ("categories", "name"),
    ("categories", "slug"),

    ("addresses", "user_id"),
    ("cart_items", "cart_id"),
    ("cart_items", "product_id"),
]


def _colunas_indexadas(tabela: str) -> set[str]:

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
