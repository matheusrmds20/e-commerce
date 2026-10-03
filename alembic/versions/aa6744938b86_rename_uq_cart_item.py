"""rename_uq_cart_item

Revision ID: aa6744938b86
Revises: 0c3b7bfca865
Create Date: 2026-10-03 16:41:00.000000

Renomeia a constraint única de ``cart_items`` de ``uq_cart_item_cart_product``
para ``unique_cart_item``, alinhando o banco ao modelo
(``models/cart_item.py`` → ``__table_args__``) e à migration ``3657bf59c715``.

Por que é necessária: a migration ``3657bf59c715`` foi alterada depois de já
ter sido aplicada neste ambiente — no banco ela criou ``uq_cart_item_cart_product``,
mas o arquivo (reescrito) e o modelo passaram a usar ``unique_cart_item``. O
``--autogenerate`` apontava a divergência (dropar a antiga / criar a nova a cada
execução).

Robustez em ambientes novos: a operação é idempotente. Se num ambiente a
migration ``3657bf59c715`` ainda estiver criando com o nome antigo
(``uq_cart_item_cart_product``), esta revisão renomeia. Se já estiver criando
com o novo (``unique_cart_item``), a coluna não existe no ``pg_constraint`` e o
``SELECT`` devolve vazio → não faz nada. Assim roda de forma segura sobre
qualquer estado anterior.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa6744938b86'
down_revision: Union[str, Sequence[str], None] = '0c3b7bfca865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    exists = bind.execute(
        sa.text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname = 'uq_cart_item_cart_product' "
            "  AND conrelid = 'cart_items'::regclass"
        )
    ).fetchone()

    # Só renomeia se o nome antigo ainda existir neste banco.
    if exists:
        op.execute(
            "ALTER TABLE cart_items "
            "RENAME CONSTRAINT uq_cart_item_cart_product "
            "TO unique_cart_item"
        )


def downgrade() -> None:
    """Volta ao nome antigo."""
    bind = op.get_bind()
    exists = bind.execute(
        sa.text(
            "SELECT 1 FROM pg_constraint "
            "WHERE conname = 'unique_cart_item' "
            "  AND conrelid = 'cart_items'::regclass"
        )
    ).fetchone()

    if exists:
        op.execute(
            "ALTER TABLE cart_items "
            "RENAME CONSTRAINT unique_cart_item "
            "TO uq_cart_item_cart_product"
        )