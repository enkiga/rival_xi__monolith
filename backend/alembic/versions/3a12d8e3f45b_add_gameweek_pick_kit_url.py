"""add gameweek pick kit url

Revision ID: 3a12d8e3f45b
Revises: 4b8c2a1f9e73
Create Date: 2026-10-04 19:15:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "3a12d8e3f45b"
down_revision: Union[str, Sequence[str], None] = "4b8c2a1f9e73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gameweek_picks",
        sa.Column("kit_url", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gameweek_picks", "kit_url")
