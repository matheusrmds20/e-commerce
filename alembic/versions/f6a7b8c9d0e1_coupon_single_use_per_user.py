"""add single_use_per_user to coupons and used_at to user_coupons

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-08 14:00:00.000000

Permite modelar cupom de **uso único por cliente** (o padrão de cupom pessoal:
"R$20 off, válido uma vez por pessoa"), que antes não era expressável:

- ``coupons.single_use_per_user``: liga a regra para o cupom;
- ``user_coupons.used_at``: quando o cliente usou o cupom (NULL = ainda não).

O ``Coupon.max_uses`` continua existindo e é o limite GLOBAL do cupom,
compartilhado entre todos os usuários — as duas regras são independentes e
podem ser combinadas.

``user_coupons.used_at`` é ``nullable``: os vínculos já existentes ficam NULL
(nunca usados), o que é o estado correto para cupons criados antes da regra.

``down_revision`` = e5f6a7b8c9d0 (add_coupon_used_count), o HEAD anterior.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona a flag de uso único e a marca de uso por cliente."""
    op.add_column(
        'coupons',
        sa.Column(
            'single_use_per_user',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )
    op.add_column(
        'user_coupons',
        sa.Column('used_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove a flag e a marca de uso."""
    op.drop_column('user_coupons', 'used_at')
    op.drop_column('coupons', 'single_use_per_user')
