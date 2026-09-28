"""newsletter_subscribers

Revision ID: a1f2e3d4c5b6
Revises: 8cf455aabd0d
Create Date: 2026-09-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f2e3d4c5b6'
down_revision: Union[str, Sequence[str], None] = '8cf455aabd0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('newsletter_subscribers',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('subscribed_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_newsletter_subscribers_id'), 'newsletter_subscribers', ['id'], unique=False)
    op.create_index(op.f('ix_newsletter_subscribers_email'), 'newsletter_subscribers', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_newsletter_subscribers_email'), table_name='newsletter_subscribers')
    op.drop_index(op.f('ix_newsletter_subscribers_id'), table_name='newsletter_subscribers')
    op.drop_table('newsletter_subscribers')
