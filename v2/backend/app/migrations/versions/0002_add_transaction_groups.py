"""add transaction_group table and effective_amount

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = "fk_transaction_transaction_group"


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if "transaction_group" not in existing_tables:
        op.create_table(
            "transaction_group",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=True),
        )

    existing_columns = {c["name"] for c in inspector.get_columns("transaction")}

    if "id_transaction_group" not in existing_columns:
        op.add_column("transaction", sa.Column("id_transaction_group", sa.Integer(), nullable=True))

    if "effective_amount" not in existing_columns:
        op.add_column("transaction", sa.Column("effective_amount", sa.Numeric(precision=20, scale=2), nullable=True))

    existing_fks = {fk["name"] for fk in inspector.get_foreign_keys("transaction") if fk["name"]}
    if FK_NAME not in existing_fks:
        op.create_foreign_key(
            FK_NAME, "transaction", "transaction_group",
            ["id_transaction_group"], ["id"], ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint(FK_NAME, "transaction", type_="foreignkey")
    op.drop_column("transaction", "effective_amount")
    op.drop_column("transaction", "id_transaction_group")
    op.drop_table("transaction_group")
