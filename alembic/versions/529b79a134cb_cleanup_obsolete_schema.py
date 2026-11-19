from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision: str = '529b79a134cb'
down_revision: Union[str, Sequence[str], None] = '083517c6acac'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Remove obsolete password reset table
    op.drop_index('ix_password_reset_tokens_id', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')

    # Correct refresh token foreign key
    op.drop_constraint(
        'refresh_tokens_user_id_fkey',
        'refresh_tokens',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'fk_refresh_tokens_user_id_users',
        'refresh_tokens',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Remove obsolete email verification fields
    op.drop_column('users', 'verification_token_hash')
    op.drop_column('users', 'verification_token_expires_at')


def downgrade() -> None:
    op.add_column(
        'users',
        sa.Column('verification_token_hash', sa.String(), nullable=True)
    )

    op.add_column(
        'users',
        sa.Column(
            'verification_token_expires_at',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.drop_constraint(
        'fk_refresh_tokens_user_id_users',
        'refresh_tokens',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'refresh_tokens_user_id_fkey',
        'refresh_tokens',
        'users',
        ['user_id'],
        ['id']
    )

    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='password_reset_tokens_user_id_fkey'
        )
    )

    op.create_index(
        'ix_password_reset_tokens_id',
        'password_reset_tokens',
        ['id']
    )

    op.create_index(
        'ix_password_reset_tokens_token',
        'password_reset_tokens',
        ['token'],
        unique=True
    )