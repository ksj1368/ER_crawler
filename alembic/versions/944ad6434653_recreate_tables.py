"""recreate_tables

Revision ID: 944ad6434653
Revises: b29c8fe45f60
Create Date: 2026-01-02 20:12:06.368160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '944ad6434653'
down_revision: Union[str, None] = 'b29c8fe45f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
