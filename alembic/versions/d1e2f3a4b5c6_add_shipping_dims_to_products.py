"""add shipping dimensions to products (Melhor Envio)

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-10-06 18:00:00.000000

Adiciona colunas de peso e dimensões ao ``products`` para a cotação de frete
via Melhor Envio (a API exige ``weight``, ``height``, ``width`` e ``length``).

Todas as colunas são ``nullable``: produtos cadastrados antes da integração não
são quebrados. A validação de presença dos dados ocorre na hora de cotar
(shipping_service), não na escrita do produto.

``down_revision`` = c1d2e3f4a5b6 (payments_unique_provider_payment), o HEAD
da cadeia de migrations antes desta.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona as colunas de envio ao ``products``."""
    op.add_column('products', sa.Column('weight_kg', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('height_cm', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('width_cm', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('length_cm', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove as colunas de envio do ``products``."""
    op.drop_column('products', 'length_cm')
    op.drop_column('products', 'width_cm')
    op.drop_column('products', 'height_cm')
    op.drop_column('products', 'weight_kg')