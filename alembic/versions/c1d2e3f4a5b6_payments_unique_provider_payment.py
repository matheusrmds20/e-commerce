"""payments_unique_provider_payment

Revision ID: c1d2e3f4a5b6
Revises: b1a2c3d4e5f6
Create Date: 2026-10-04 13:00:00.000000

Adiciona a constraint única em ``payments(provider, provider_payment_id)``
que já existia no model (``Payment.__table_args__``) mas nunca foi criada
por uma migration. A tabela ``payments`` foi criada em
``a0091f7e1f03`` sem essa constraint.

A exclusividade é importante para o ``process_webhook``: cada combinação de
provedor + id do pagamento deve aparecer uma única vez, e o reenvio do
webhook (que o Mercado Pago faz por até ~15 min) não deve gerar duplicidade.

provider_payment_id é nullable. No Postgres, NULLs não conflitam numa
constraint única (cada linha NULL é distinta), então linha(s) com
provider_payment_id NULL não impedem a criação nem causam falsos conflitos.

Safe para tabelas com dados (sem duplicatas): a migration usa o padrão de
create + validação apenas se necessário.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "payments_order_provider_payment_id_key",
        "payments",
        ["provider", "provider_payment_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "payments_order_provider_payment_id_key",
        "payments",
        type_="unique",
    )