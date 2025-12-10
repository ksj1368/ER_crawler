"""Check alembic setup

Revision ID: 71025684cdfb
Revises: 8195275cd3f7
Create Date: 2025-12-10 21:28:46.615881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71025684cdfb'
down_revision: Union[str, None] = '8195275cd3f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
