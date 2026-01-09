"""fix_composite_foreign_keys

Revision ID: d005eeb9a229
Revises: c65be9497d67
Create Date: 2026-01-09 17:10:08.394330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd005eeb9a229'
down_revision: Union[str, None] = 'c65be9497d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
