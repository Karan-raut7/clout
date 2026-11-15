"""add direct messages

Revision ID: 57b807e71666
Revises: 6d15fee9a123
Create Date: 2026-11-14 12:03:58.993951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57b807e71666'
down_revision: Union[str, Sequence[str], None] = '6d15fee9a123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'rooms',
        sa.Column('is_direct', sa.Boolean(), server_default='false', nullable=False)
    )
    op.alter_column(
        'rooms', 'name',
        existing_type=sa.VARCHAR(),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'rooms', 'name',
        existing_type=sa.VARCHAR(),
        nullable=False
    )
    op.drop_column('rooms', 'is_direct')