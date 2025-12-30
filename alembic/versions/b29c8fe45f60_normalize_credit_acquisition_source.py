"""Normalize credit acquisition source

Revision ID: b29c8fe45f60
Revises: a18b7ed34e59
Create Date: 2025-12-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b29c8fe45f60'
down_revision: Union[str, None] = '71025684cdfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    print("DEBUG: Executing upgrade() in b29c8fe45f60")
    # 1. Create credit_acquisition_source table
    op.create_table(
        'credit_acquisition_source',
        sa.Column('source_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_name', sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint('source_id'),
        sa.UniqueConstraint('source_name')
    )

    # 2. Add acquisition_source_id column to match_user_credit_acquisitions
    op.add_column('match_user_credit_acquisitions', sa.Column('acquisition_source_id', sa.Integer(), nullable=True))

    # 3. Migrate Data
    conn = op.get_bind()
    
    # Insert existing unique sources into the new table
    # We use raw SQL for MySQL compatibility (INSERT IGNORE)
    conn.execute(sa.text("""
        INSERT IGNORE INTO credit_acquisition_source (source_name)
        SELECT DISTINCT acquisition_source FROM match_user_credit_acquisitions
    """))
    
    # Update the new column with IDs
    conn.execute(sa.text("""
        UPDATE match_user_credit_acquisitions m
        JOIN credit_acquisition_source c ON m.acquisition_source = c.source_name
        SET m.acquisition_source_id = c.source_id
    """))

    # 4. Modify Schema
    # Drop old Primary Key (MySQL specific name is usually PRIMARY)
    # We handle this inside a try-except block in case of naming issues, 
    # but strictly speaking 'PRIMARY' is the name in MySQL.
    try:
        op.drop_constraint('PRIMARY', 'match_user_credit_acquisitions', type_='primary')
    except Exception as e:
        print(f"Warning: Could not drop PK by name 'PRIMARY': {e}")
        # If the PK has a different name (unlikely for MySQL), this needs manual intervention.

    # Drop old column
    op.drop_column('match_user_credit_acquisitions', 'acquisition_source')

    # Alter new column to NOT NULL
    op.alter_column('match_user_credit_acquisitions', 'acquisition_source_id', nullable=False, existing_type=sa.Integer())

    # Create new Primary Key
    op.create_primary_key(
        'pk_match_user_credit_acquisitions',
        'match_user_credit_acquisitions',
        ['match_id', 'uid', 'acquisition_source_id']
    )

    # Create Foreign Key
    op.create_foreign_key(
        'fk_muc_acquisition_source',
        'match_user_credit_acquisitions',
        'credit_acquisition_source',
        ['acquisition_source_id'],
        ['source_id']
    )


def downgrade() -> None:
    # 1. Add old column back
    op.add_column('match_user_credit_acquisitions', sa.Column('acquisition_source', sa.String(length=32), nullable=True))

    # 2. Populate old column from IDs
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE match_user_credit_acquisitions m
        JOIN credit_acquisition_source c ON m.acquisition_source_id = c.source_id
        SET m.acquisition_source = c.source_name
    """))

    # 3. Drop FK
    op.drop_constraint('fk_muc_acquisition_source', 'match_user_credit_acquisitions', type_='foreignkey')

    # 4. Drop new PK
    op.drop_constraint('pk_match_user_credit_acquisitions', 'match_user_credit_acquisitions', type_='primary')

    # 5. Drop new column
    op.drop_column('match_user_credit_acquisitions', 'acquisition_source_id')

    # 6. Re-create old PK
    # Note: acquisition_source length was 32 originally.
    op.alter_column('match_user_credit_acquisitions', 'acquisition_source', nullable=False, existing_type=sa.String(length=32))
    op.create_primary_key(
        'PRIMARY', # Re-using standard name
        'match_user_credit_acquisitions',
        ['match_id', 'uid', 'acquisition_source']
    )

    # 7. Drop new table
    op.drop_table('credit_acquisition_source')
