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
    """Existing tables were created by Base.metadata.create_all().

    This migration exists so that subsequent migrations have a base to build on.
    For a fresh database, run create_all first, then stamp this revision.
    """
    pass


def downgrade() -> None:
    pass
