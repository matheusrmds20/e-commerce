"""unique_cart_per_user

Revision ID: 0c3b7bfca865
Revises: 3657bf59c715
Create Date: 2026-10-03 16:25:08.091568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c3b7bfca865'
down_revision: Union[str, Sequence[str], None] = '3657bf59c715'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Garante um carrinho por usuário (constraint unique em ``carts.user_id``).

    Nome alinhado com o ``__table_args__`` do model Cart (``carts_user_id_key``),
    senão o próximo ``--autogenerate`` trocaria o nome.

    Ao contrário da migration de ``cart_items``, **não** há dedup automático:
    fundir dois carrinhos é destrutivo (não dá para saber a qual carrinho cada
    item pertence). Se o banco tiver ``user_id`` repetido, a migration falha
    com mensagem clara antes de tentar criar a constraint.
    """
    duplicados = op.get_bind().execute(
        sa.text(
            "SELECT user_id, COUNT(*) FROM carts "
            "GROUP BY user_id HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if duplicados:
        raise RuntimeError(
            "Não foi possível criar a constraint única de carts.user_id: "
            f"usuários com mais de um carrinho encontrados: {duplicados}. "
            "Consolide ou apague os carrinhos duplicados e rode a migration "
            "novamente."
        )

    op.create_unique_constraint("carts_user_id_key", "carts", ["user_id"])


def downgrade() -> None:
    """Remove a unicidade de ``carts.user_id``."""
    op.drop_constraint("carts_user_id_key", "carts", type_="unique")
