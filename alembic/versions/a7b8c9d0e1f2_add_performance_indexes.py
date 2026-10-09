"""add indexes on hot filter/join columns

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-10-08 15:00:00.000000

Cria índices nas colunas usadas com mais frequência em ``WHERE``/``JOIN``/
``ORDER BY``. O Postgres NÃO indexa chaves estrangeiras automaticamente, então
essas colunas faziam sequential scan — o custo crescia junto com a tabela.

Índices adicionados (nome explícito ``ix_<tabela>_<coluna>``):
- ``orders``: user_id, address_id, status, created_at
- ``order_items``: order_id, product_id
- ``payments``: order_id
- ``reviews``: user_id, product_id
- ``wishlists``: user_id, product_id
- ``products``: category_id, slug
- ``categories``: name, slug
- ``addresses``: user_id
- ``cart_items``: cart_id, product_id
- ``coupons``: product_id

``payments.provider_payment_id`` já é coberto pela unique
``(provider, provider_payment_id)`` para lookups que informam o provider; o
lookup do webhook filtra só por ``provider_payment_id``, então ganha índice
próprio.

``create_index`` usa ``if_not_exists=True`` para a migration ser idempotente em
bancos que já tenham algum destes índices criado manualmente.

``down_revision`` = f6a7b8c9d0e1 (coupon_single_use_per_user), o HEAD anterior.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (tabela, coluna) — cada um vira um índice simples.
INDICES = [
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
    ("coupons", "product_id"),
]


def upgrade() -> None:
    """Cria os índices (idempotente via ``if_not_exists``)."""
    for tabela, coluna in INDICES:
        op.create_index(
            f"ix_{tabela}_{coluna}",
            tabela,
            [coluna],
            if_not_exists=True,
        )


def downgrade() -> None:
    """Remove os índices criados por esta migration."""
    for tabela, coluna in INDICES:
        op.drop_index(
            f"ix_{tabela}_{coluna}",
            table_name=tabela,
            if_exists=True,
        )
