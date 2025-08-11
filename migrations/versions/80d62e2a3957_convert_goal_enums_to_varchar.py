"""convert_goal_enums_to_varchar

Revision ID: 80d62e2a3957
Revises: 91155436e1ab
Create Date: 2025-08-11 17:48:31.022574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80d62e2a3957'
down_revision: Union[str, Sequence[str], None] = '91155436e1ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert goal enum columns to varchar to remove enum validation."""
    # Convert goal type column to varchar
    op.execute("ALTER TABLE goals ALTER COLUMN type TYPE VARCHAR")
    
    # Convert goal status column to varchar
    op.execute("ALTER TABLE goals ALTER COLUMN status TYPE VARCHAR")
    
    # Convert goal phase column to varchar
    op.execute("ALTER TABLE goals ALTER COLUMN phase TYPE VARCHAR")
    
    # Convert goal priority column to varchar
    op.execute("ALTER TABLE goals ALTER COLUMN priority TYPE VARCHAR")
    
    # Drop the enum types since they're no longer used
    op.execute("DROP TYPE IF EXISTS goaltypeenum")
    op.execute("DROP TYPE IF EXISTS statusenum")
    op.execute("DROP TYPE IF EXISTS phaseenum")
    op.execute("DROP TYPE IF EXISTS priorityenum")


def downgrade() -> None:
    """Revert back to enum types (if needed)."""
    # Recreate enum types
    op.execute("CREATE TYPE goaltypeenum AS ENUM ('YEARLY', 'QUARTERLY', 'MONTHLY', 'WEEKLY')")
    op.execute("CREATE TYPE statusenum AS ENUM ('ACTIVE', 'COMPLETED', 'PAUSED')")
    op.execute("CREATE TYPE phaseenum AS ENUM ('Research', 'MVP', 'Growth', 'Scale', 'Transition')")
    op.execute("CREATE TYPE priorityenum AS ENUM ('HIGH', 'MEDIUM', 'LOW')")
    
    # Convert columns back to enum types
    op.execute("ALTER TABLE goals ALTER COLUMN type TYPE goaltypeenum USING type::goaltypeenum")
    op.execute("ALTER TABLE goals ALTER COLUMN status TYPE statusenum USING status::statusenum")
    op.execute("ALTER TABLE goals ALTER COLUMN phase TYPE phaseenum USING phase::phaseenum")
    op.execute("ALTER TABLE goals ALTER COLUMN priority TYPE priorityenum USING priority::priorityenum")
