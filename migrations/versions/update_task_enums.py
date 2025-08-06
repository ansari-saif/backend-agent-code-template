"""Update task enum types to use proper casing

Revision ID: update_task_enums
Revises: 9ae0f8ccfe7f
Create Date: 2024-03-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_task_enums'
down_revision = '9ae0f8ccfe7f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Convert columns to varchar temporarily
    op.execute("ALTER TABLE tasks ALTER COLUMN energy_required TYPE VARCHAR")
    op.execute("ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR")
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE VARCHAR")
    
    # Drop existing enum types
    op.execute("DROP TYPE IF EXISTS energyrequiredenum")
    op.execute("DROP TYPE IF EXISTS taskpriorityenum")
    op.execute("DROP TYPE IF EXISTS completionstatusenum")
    
    # Create new enum types with proper casing
    op.execute("CREATE TYPE energyrequiredenum AS ENUM ('High', 'Medium', 'Low')")
    op.execute("CREATE TYPE taskpriorityenum AS ENUM ('Urgent', 'High', 'Medium', 'Low')")
    op.execute("CREATE TYPE completionstatusenum AS ENUM ('Pending', 'In Progress', 'Completed', 'Cancelled')")
    
    # Convert columns back to enum types
    op.execute("ALTER TABLE tasks ALTER COLUMN energy_required TYPE energyrequiredenum USING energy_required::energyrequiredenum")
    op.execute("ALTER TABLE tasks ALTER COLUMN priority TYPE taskpriorityenum USING priority::taskpriorityenum")
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE completionstatusenum USING completion_status::completionstatusenum")

def downgrade() -> None:
    # Convert back to varchar if needed
    op.execute("ALTER TABLE tasks ALTER COLUMN energy_required TYPE VARCHAR")
    op.execute("ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR")
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE VARCHAR")
    
    op.execute("DROP TYPE IF EXISTS energyrequiredenum")
    op.execute("DROP TYPE IF EXISTS taskpriorityenum")
    op.execute("DROP TYPE IF EXISTS completionstatusenum")