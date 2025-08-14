"""merge heads

Revision ID: 3e1f5cbc98ef
Revises: a1b2c3d4e5f6, da6ec41d3d52
Create Date: 2025-08-14 19:44:01.737567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e1f5cbc98ef'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'da6ec41d3d52')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
