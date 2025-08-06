"""update_task_enum_types

Revision ID: 9ae0f8ccfe7f
Revises: a46875193abc
Create Date: 2025-08-07 00:33:10.642142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ae0f8ccfe7f'
down_revision: Union[str, Sequence[str], None] = 'a46875193abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
