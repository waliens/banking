"""add transaction description

Revision ID: 1ac3ef49516b
Revises: f4f90ab77b43
Create Date: 2025-03-02 14:06:51.863636

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ac3ef49516b'
down_revision = 'f4f90ab77b43'
branch_labels = None
depends_on = None


def upgrade():
    # Add the new column
    op.add_column('transaction', sa.Column('description', sa.String(), nullable=True, server_default=""))

    # Backfill the new column using SQL statements
    connection = op.get_bind()

    # Update description for data_source 'ing'
    connection.execute(sa.text("""
        UPDATE transaction
        SET description = COALESCE(metadata->>'details', metadata->>'communication', '')
        WHERE data_source = 'ing'
    """))

    # Update description for data_source 'belfius'
    connection.execute(sa.text("""
        UPDATE transaction
        SET description = COALESCE(metadata->>'communication', metadata->>'transaction', '')
        WHERE data_source = 'belfius'
    """))


def downgrade():
    # Remove the column
    op.drop_column('transaction', 'description')
