"""Primeira

Revision ID: dfaa470fc553
Revises: fb4e3ed8eb4c
Create Date: 2026-09-18 17:09:29.873869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfaa470fc553'
down_revision: Union[str, Sequence[str], None] = 'fb4e3ed8eb4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Adiciona as flags de curadoria da Home.

    Por que não usar `op.add_column(..., nullable=False)` direto: o Postgres
    recusa adicionar uma coluna NOT NULL a uma tabela que já tenha linhas,
    porque não saberia qual valor colocar nas linhas existentes. Mesmo que a
    tabela esteja vazia no seu ambiente agora, a migration precisa ser segura
    em qualquer ambiente (inclusive produção com dados).

    Padrão de 3 passos: adiciona nullable → preenche → torna NOT NULL.
    """
    # 1) Adiciona as colunas como nuláveis.
    op.add_column(
        "products",
        sa.Column("is_featured", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("is_bestseller", sa.Boolean(), nullable=True),
    )

    # 2) Preenche as linhas existentes com o valor padrão.
    op.execute("UPDATE products SET is_featured = false WHERE is_featured IS NULL")
    op.execute(
        "UPDATE products SET is_bestseller = false WHERE is_bestseller IS NULL"
    )

    # 3) Aplica NOT NULL e define o default no banco para novas linhas.
    op.alter_column(
        "products",
        "is_featured",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )
    op.alter_column(
        "products",
        "is_bestseller",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("products", "is_bestseller")
    op.drop_column("products", "is_featured")
