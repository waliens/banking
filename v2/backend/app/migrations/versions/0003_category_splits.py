"""replace id_category with category_split table

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if "category_split" not in existing_tables:
        op.create_table(
            "category_split",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("id_transaction", sa.Integer(), sa.ForeignKey("transaction.id", ondelete="CASCADE"), nullable=True),
            sa.Column("id_group", sa.Integer(), sa.ForeignKey("transaction_group.id", ondelete="CASCADE"), nullable=True),
            sa.Column("id_category", sa.Integer(), sa.ForeignKey("category.id", ondelete="CASCADE"), nullable=False),
            sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        )

    # Migrate existing id_category data to category_split rows
    # Only for standalone transactions (not in a group)
    existing_columns = {c["name"] for c in inspector.get_columns("transaction")}
    if "id_category" in existing_columns:
        op.execute(
            """
            INSERT INTO category_split (id_transaction, id_category, amount)
            SELECT id, id_category, COALESCE(effective_amount, amount)
            FROM transaction
            WHERE id_category IS NOT NULL
              AND id_transaction_group IS NULL
            """
        )

        # Drop the id_category column
        op.drop_column("transaction", "id_category")


def downgrade() -> None:
    op.add_column("transaction", sa.Column("id_category", sa.Integer(), sa.ForeignKey("category.id", ondelete="SET NULL"), nullable=True))

    # Restore single-split data back to id_category
    op.execute(
        """
        UPDATE transaction SET id_category = cs.id_category
        FROM category_split cs
        WHERE cs.id_transaction = transaction.id
    """
    )

    op.drop_table("category_split")
