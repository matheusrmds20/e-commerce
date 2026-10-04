"""order_receipt_path

Revision ID: b1a2c3d4e5f6
Revises: aa6744938b86
Create Date: 2026-10-04 12:00:00.000000

Adiciona a coluna ``orders.receipt_path`` que armazena o caminho relativo do
arquivo PDF do comprovante/recibo do pedido. A coluna é nullable porque o
comprovante é gerado de forma assíncrona (task Celery) APÓS a criação do pedido.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'aa6744938b86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "orders",
        sa.Column("receipt_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("orders", "receipt_path")