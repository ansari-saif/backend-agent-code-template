"""Add IST to timezone enum

Revision ID: a46875193abc
Revises: 
Create Date: 2024-03-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a46875193abc'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # First, drop the existing enum type constraints
    op.execute("ALTER TABLE users ALTER COLUMN timezone TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS timezoneenum")
    
    # Create the enum type with all values
    op.execute("CREATE TYPE timezoneenum AS ENUM ('UTC', 'EST', 'PST', 'CST', 'MST', 'IST')")
    
    # Alter the column to use the new enum type
    op.execute("ALTER TABLE users ALTER COLUMN timezone TYPE timezoneenum USING timezone::timezoneenum")

def downgrade() -> None:
    # Convert back to varchar if needed
    op.execute("ALTER TABLE users ALTER COLUMN timezone TYPE VARCHAR")
    op.execute("DROP TYPE IF EXISTS timezoneenum")
