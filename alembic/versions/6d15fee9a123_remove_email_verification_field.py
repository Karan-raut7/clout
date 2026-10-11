"""remove email verification field

Revision ID: 6d15fee9a123
Revises: d9dc39c901b0
Create Date: 2026-10-11 07:17:20.550575
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d15fee9a123"
down_revision: Union[str, Sequence[str], None] = "d9dc39c901b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "is_verified")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )