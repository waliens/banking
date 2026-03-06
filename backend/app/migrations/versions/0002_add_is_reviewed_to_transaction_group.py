"""add is_reviewed to transaction_group

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("transaction_group")]
    if "is_reviewed" not in columns:
        op.add_column(
            "transaction_group",
            sa.Column("is_reviewed", sa.Boolean(), server_default="false", nullable=False),
        )


def downgrade() -> None:
    op.drop_column("transaction_group", "is_reviewed")
