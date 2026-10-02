"""mercado pago (payments)

Revision ID: a0091f7e1f03
Revises: a1f2e3d4c5b6
Create Date: 2026-09-29 18:30:43.696965

Cria a tabela ``payments`` usada pelo módulo de pagamentos (Mercado Pago).

Contexto da correção: esta revisão havia sido autogerada quando o model
``Payment`` ainda não estava importado em ``alembic/env.py``. Sem o model
registrado, o autogenerate não enxergou a tabela ausente e, em vez disso,
gerou o DROP de ``newsletter_subscribers`` — que existe em código
(``NewsletterSubscriber``), está roteado em ``/newsletter`` e coberto por
testes. Ou seja, a migração original quebrou uma feature viva e deixou o banco
marcado em ``head`` sem a tabela ``payments`` (toda consulta estourava
``UndefinedTable``).

Esta revisão agora:
- cria ``payments`` (idempotente);
- garante que ``newsletter_subscribers`` exista (recria caso o DROP original
  já tenha rodado em algum ambiente).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0091f7e1f03'
down_revision: Union[str, Sequence[str], None] = 'a1f2e3d4c5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tabelas = set(insp.get_table_names())

    # Cria a tabela de pagamentos (idempotente para bancos parcialmente migrados).
    if 'payments' not in tabelas:
        op.create_table(
            'payments',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('provider', sa.String(length=255), nullable=False),
            sa.Column('provider_payment_id', sa.String(length=255), nullable=True),
            sa.Column('provider_preference_id', sa.String(length=255), nullable=True),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False),
            sa.Column('status', sa.String(length=255), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)

    # Restaura newsletter_subscribers caso o DROP da revisão original tenha
    # rodado (a feature continua ativa em código).
    if 'newsletter_subscribers' not in tabelas:
        op.create_table(
            'newsletter_subscribers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('subscribed_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(
            op.f('ix_newsletter_subscribers_id'),
            'newsletter_subscribers',
            ['id'],
            unique=False,
        )
        op.create_index(
            op.f('ix_newsletter_subscribers_email'),
            'newsletter_subscribers',
            ['email'],
            unique=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if 'payments' in insp.get_table_names():
        op.drop_index(op.f('ix_payments_id'), table_name='payments')
        op.drop_table('payments')
