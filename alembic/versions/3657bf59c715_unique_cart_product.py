"""unique_cart_product

Revision ID: 3657bf59c715
Revises: a0091f7e1f03
Create Date: 2026-10-03 15:33:28.709388

Torna explícito no banco o invariante de domínio do carrinho: **no máximo uma
linha por produto em cada carrinho** (o fluxo já atualiza quantidade via
``get_by_cart_and_product``/``update_item``). Antes, a proteção contra item
duplicado era implícita — dependia da ordem ``FOR UPDATE`` no
``ProductRepository`` dentro do ``CartService.add_item`` — e qualquer caminho
que inserisse ``cart_item`` sem o lock duplicaria linhas silenciosamente.

Passos do ``upgrade``:

1. **Deduplica** linhas existentes — soma as quantidades dos duplicados na
   linha sobrevivente (menor id) e apaga as demais. Sem isso, a constraint
   falharia em bancos onde a race já gerou itens repetidos.
2. **Cria** a constraint única ``(cart_id, product_id)``.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3657bf59c715'
down_revision: Union[str, Sequence[str], None] = 'a0091f7e1f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Soma as quantidades das linhas duplicadas na sobrevivente (menor id).
    #    WHERE ... <> ... é só para não reescrever linhas já corretas.
    op.execute(
        """
        UPDATE cart_items
        SET quantity = sub.total_qty
        FROM (
            SELECT cart_id, product_id, MIN(id) AS keep_id, SUM(quantity) AS total_qty
            FROM cart_items
            GROUP BY cart_id, product_id
        ) sub
        WHERE cart_items.id = sub.keep_id
          AND cart_items.quantity <> sub.total_qty
        """
    )

    # 2. Remove as demais (qualquer linha com (cart_id, product_id) repetido e id maior).
    op.execute(
        """
        DELETE FROM cart_items ci
        USING cart_items ci2
        WHERE ci.id > ci2.id
          AND ci.cart_id = ci2.cart_id
          AND ci.product_id = ci2.product_id
        """
    )

    # 3. Constraint única: um (cart_id, product_id) por linha — ponto final.
    #    Nome alinhado com o `__table_args__` do model CartItem
    #    (unique_cart_item), senão o próximo `--autogenerate` trocaria o nome.
    op.create_unique_constraint(
        "unique_cart_item", "cart_items", ["cart_id", "product_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("unique_cart_item", "cart_items", type_="unique")