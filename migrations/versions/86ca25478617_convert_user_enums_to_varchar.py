"""convert_user_enums_to_varchar

Revision ID: 86ca25478617
Revises: 7c1d81f56760
Create Date: 2025-08-11 17:50:15.022574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86ca25478617'
down_revision: Union[str, Sequence[str], None] = '7c1d81f56760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert user enum columns to varchar to remove enum validation."""
    # Convert user timezone column to varchar
    op.execute("ALTER TABLE users ALTER COLUMN timezone TYPE VARCHAR")
    
    # Convert user current_phase column to varchar
    op.execute("ALTER TABLE users ALTER COLUMN current_phase TYPE VARCHAR")
    
    # Convert user energy_profile column to varchar
    op.execute("ALTER TABLE users ALTER COLUMN energy_profile TYPE VARCHAR")
    
    # Drop the enum types since they're no longer used
    op.execute("DROP TYPE IF EXISTS timezoneenum")
    op.execute("DROP TYPE IF EXISTS phaseenum_user")
    op.execute("DROP TYPE IF EXISTS energyprofileenum")


def downgrade() -> None:
    """Revert back to enum types (if needed)."""
    # Recreate enum types
    op.execute("CREATE TYPE timezoneenum AS ENUM ('UTC', 'EST', 'PST', 'CST', 'MST', 'IST')")
    op.execute("CREATE TYPE phaseenum_user AS ENUM ('Research', 'MVP', 'Growth', 'Scale', 'Transition')")
    op.execute("CREATE TYPE energyprofileenum AS ENUM ('Morning', 'Afternoon', 'Evening')")
    
    # Convert columns back to enum types
    op.execute("ALTER TABLE users ALTER COLUMN timezone TYPE timezoneenum USING timezone::timezoneenum")
    op.execute("ALTER TABLE users ALTER COLUMN current_phase TYPE phaseenum_user USING current_phase::phaseenum_user")
    op.execute("ALTER TABLE users ALTER COLUMN energy_profile TYPE energyprofileenum USING energy_profile::energyprofileenum")
