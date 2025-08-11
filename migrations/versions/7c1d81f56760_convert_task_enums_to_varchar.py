"""convert_task_enums_to_varchar

Revision ID: 7c1d81f56760
Revises: 80d62e2a3957
Create Date: 2025-08-11 17:49:45.022574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1d81f56760'
down_revision: Union[str, Sequence[str], None] = '80d62e2a3957'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert task enum columns to varchar to remove enum validation."""
    # Convert task priority column to varchar
    op.execute("ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR")
    
    # Convert task completion_status column to varchar
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE VARCHAR")
    
    # Convert task energy_required column to varchar
    op.execute("ALTER TABLE tasks ALTER COLUMN energy_required TYPE VARCHAR")
    
    # Drop the enum types since they're no longer used
    op.execute("DROP TYPE IF EXISTS taskpriorityenum")
    op.execute("DROP TYPE IF EXISTS completionstatusenum")
    op.execute("DROP TYPE IF EXISTS energyrequiredenum")


def downgrade() -> None:
    """Revert back to enum types (if needed)."""
    # Recreate enum types
    op.execute("CREATE TYPE taskpriorityenum AS ENUM ('Urgent', 'High', 'Medium', 'Low')")
    op.execute("CREATE TYPE completionstatusenum AS ENUM ('Pending', 'In Progress', 'Completed', 'Cancelled')")
    op.execute("CREATE TYPE energyrequiredenum AS ENUM ('High', 'Medium', 'Low')")
    
    # Convert columns back to enum types
    op.execute("ALTER TABLE tasks ALTER COLUMN priority TYPE taskpriorityenum USING priority::taskpriorityenum")
    op.execute("ALTER TABLE tasks ALTER COLUMN completion_status TYPE completionstatusenum USING completion_status::completionstatusenum")
    op.execute("ALTER TABLE tasks ALTER COLUMN energy_required TYPE energyrequiredenum USING energy_required::energyrequiredenum")
