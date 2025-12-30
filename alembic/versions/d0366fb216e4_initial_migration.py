"""initial migration

Revision ID: d0366fb216e4
Revises: b29c8fe45f60
Create Date: 2025-12-30 20:09:16.903035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0366fb216e4'
down_revision: Union[str, None] = 'b29c8fe45f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
