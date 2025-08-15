"""add_parent_goal_id_to_goals_simple

Revision ID: add_parent_goal_id_simple
Revises: 3e1f5cbc98ef
Create Date: 2025-08-15 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_parent_goal_id_simple'
down_revision: Union[str, Sequence[str], None] = '3e1f5cbc98ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add parent_goal_id column to goals table."""
    op.add_column('goals', sa.Column('parent_goal_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_goals_parent_goal_id', 
        'goals', 
        'goals', 
        ['parent_goal_id'], 
        ['goal_id']
    )


def downgrade() -> None:
    """Remove parent_goal_id column from goals table."""
    op.drop_constraint('fk_goals_parent_goal_id', 'goals', type_='foreignkey')
    op.drop_column('goals', 'parent_goal_id')
