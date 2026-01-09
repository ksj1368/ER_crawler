"""add_match_user_gadget

Revision ID: c65be9497d67
Revises: 703e1ff44d84
Create Date: 2026-01-08 11:05:41.622812

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c65be9497d67'
down_revision: Union[str, None] = '703e1ff44d84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('match_user_gadget',
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('user_num', sa.Integer(), nullable=False),
    sa.Column('gadget_id', sa.Integer(), nullable=False),
    sa.Column('gadget_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['match_user_start.match_id'], ),
    sa.ForeignKeyConstraint(['user_num'], ['match_user_start.user_num'], ),
    sa.PrimaryKeyConstraint('match_id', 'user_num', 'gadget_id')
    )


def downgrade() -> None:
    op.drop_table('match_user_gadget')
