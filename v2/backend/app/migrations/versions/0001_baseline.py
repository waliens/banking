"""baseline — stamp existing schema

Revision ID: 0001
Revises:
Create Date: 2026-02-16
"""

from typing import Sequence, Union


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """All tables are created by Base.metadata.create_all() before Alembic runs.

    This single baseline migration exists so Alembic can track schema state.
    For a fresh database, create_all runs first, then this revision is stamped.
    """
    pass


def downgrade() -> None:
    pass
