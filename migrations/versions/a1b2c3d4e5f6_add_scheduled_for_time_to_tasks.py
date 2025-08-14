"""add scheduled_for_time to tasks

Revision ID: a1b2c3d4e5f6
Revises: 91155436e1ab
Create Date: 2025-08-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '91155436e1ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by adding scheduled_for_time column."""
    op.add_column('tasks', sa.Column('scheduled_for_time', sa.Time(), nullable=True))


def downgrade() -> None:
    """Downgrade schema by removing scheduled_for_time column."""
    op.drop_column('tasks', 'scheduled_for_time')


