"""add_discard_message_to_tasks_simple

Revision ID: da6ec41d3d52
Revises: 86ca25478617
Create Date: 2025-08-11 21:06:18.101090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da6ec41d3d52'
down_revision: Union[str, Sequence[str], None] = '86ca25478617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add discard_message column to tasks table
    op.add_column('tasks', sa.Column('discard_message', sa.String(), nullable=True))
    
    # Update completion_status enum to include 'Discarded'
    # First, create the new enum type
    op.execute("CREATE TYPE completionstatusenum_new AS ENUM ('Pending', 'In Progress', 'Completed', 'Cancelled', 'Discarded')")
    
    # Update existing values to use the new enum
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE completionstatusenum_new USING completion_status::text::completionstatusenum_new")
    
    # Drop the old enum type
    op.execute("DROP TYPE completionstatusenum")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE completionstatusenum_new RENAME TO completionstatusenum")


def downgrade() -> None:
    """Downgrade schema."""
    # Revert completion_status enum to exclude 'Discarded'
    op.execute("CREATE TYPE completionstatusenum_old AS ENUM ('Pending', 'In Progress', 'Completed', 'Cancelled')")
    
    # Update existing values to use the old enum (this will fail if there are 'Discarded' values)
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE completionstatusenum_old USING completion_status::text::completionstatusenum_old")
    
    # Drop the new enum type
    op.execute("DROP TYPE completionstatusenum")
    
    # Rename the old enum type to the original name
    op.execute("ALTER TYPE completionstatusenum_old RENAME TO completionstatusenum")
    
    # Drop discard_message column
    op.drop_column('tasks', 'discard_message')
