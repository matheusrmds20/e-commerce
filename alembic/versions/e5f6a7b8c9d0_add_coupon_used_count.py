"""add used_count to coupons

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
Create Date: 2026-10-08 13:00:00.000000

Adiciona o contador ``used_count`` ao ``coupons``.

Motivo: ``max_uses`` já existia no schema mas NUNCA era lido em lugar nenhum —
um cupom podia ser aplicado infinitas vezes, mesmo com um limite cadastrado.
O contador abaixo é incrementado dentro da transação do checkout, com a linha
do cupom travada (``SELECT ... FOR UPDATE``), o que também fecha a corrida em
que dois pedidos concorrentes passavam na validação de limite.

Backfill: cupons já existentes começam em 0. Não é possível reconstruir com
precisão quantos usos ocorreram no passado (não havia registro), então optou-se
por não inventar um valor — o ``server_default='0'`` cobre as linhas antigas.

``down_revision`` = d1e2f3a4b5c6 (add_shipping_dims_to_products), o HEAD da
cadeia de migrations antes desta.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona ``coupons.used_count`` (NOT NULL, default 0)."""
    op.add_column(
        'coupons',
        sa.Column(
            'used_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )


def downgrade() -> None:
    """Remove ``coupons.used_count``."""
    op.drop_column('coupons', 'used_count')
