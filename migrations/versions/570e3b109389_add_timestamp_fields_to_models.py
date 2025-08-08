"""add timestamp fields to models

Revision ID: 570e3b109389
Revises: a78ac56124b2
Create Date: 2025-08-08 22:03:19.853934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '570e3b109389'
down_revision: Union[str, Sequence[str], None] = 'a78ac56124b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add created_at and updated_at to users table
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Add created_at and updated_at to goals table
    op.add_column('goals', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('goals', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Add created_at and updated_at to progress_logs table
    op.add_column('progress_logs', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('progress_logs', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))

    # Add created_at and updated_at to day_logs table
    op.add_column('day_logs', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('day_logs', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove created_at and updated_at from users table
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')

    # Remove created_at and updated_at from goals table
    op.drop_column('goals', 'updated_at')
    op.drop_column('goals', 'created_at')

    # Remove created_at and updated_at from progress_logs table
    op.drop_column('progress_logs', 'updated_at')
    op.drop_column('progress_logs', 'created_at')

    # Remove created_at and updated_at from day_logs table
    op.drop_column('day_logs', 'updated_at')
    op.drop_column('day_logs', 'created_at')
