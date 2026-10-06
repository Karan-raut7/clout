"""add email verification fields

Revision ID: d9dc39c901b0
Revises: 
Create Date: 2026-10-05 11:57:32.032820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9dc39c901b0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'verification_token_hash',
            sa.String(),
            nullable=True
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'verification_token_expires_at',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column(
        'users',
        'verification_token_expires_at'
    )

    op.drop_column(
        'users',
        'verification_token_hash'
    )

    op.drop_column(
        'users',
        'is_verified'
    )