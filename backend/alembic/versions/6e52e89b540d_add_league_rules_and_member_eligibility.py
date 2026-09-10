"""add league rules and member eligibility

Revision ID: 6e52e89b540d
Revises: ab69316bb1d5
Create Date: 2026-09-09 16:27:22.731651
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "6e52e89b540d"
down_revision: Union[str, Sequence[str], None] = "ab69316bb1d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Replace old league status enum.
    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status DROP DEFAULT
        """
    )

    op.execute(
        """
        CREATE TYPE league_status_new
        AS ENUM ('DRAFT', 'ACTIVE')
        """
    )

    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status
        TYPE league_status_new
        USING (
            CASE status::text
                WHEN 'SETUP' THEN 'DRAFT'
                WHEN 'ACTIVE' THEN 'ACTIVE'
                WHEN 'COMPLETED' THEN 'ACTIVE'
            END
        )::league_status_new
        """
    )

    op.execute(
        """
        DROP TYPE league_status
        """
    )

    op.execute(
        """
        ALTER TYPE league_status_new
        RENAME TO league_status
        """
    )

    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status
        SET DEFAULT 'DRAFT'::league_status
        """
    )

    # 2. League rules.
    op.create_table(
        "league_rules",
        sa.Column(
            "league_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "start_gameweek",
            sa.SmallInteger(),
            nullable=False,
        ),
        sa.Column(
            "include_transfer_deductions",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "allowed_chips",
            postgresql.ARRAY(
                sa.String(length=32)
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "start_gameweek BETWEEN 1 AND 38",
            name="ck_league_rules_start_gameweek",
        ),
        sa.ForeignKeyConstraint(
            ["league_id"],
            ["leagues.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "league_id",
        ),
    )

    # 3. Member scoring eligibility.
    op.add_column(
        "league_members",
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "league_members",
        sa.Column(
            "scoring_start_gameweek",
            sa.SmallInteger(),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_league_member_scoring_start_gameweek",
        "league_members",
        """
        scoring_start_gameweek IS NULL
        OR scoring_start_gameweek BETWEEN 1 AND 38
        """,
    )


def downgrade() -> None:
    # 1. Remove member eligibility fields.
    op.drop_constraint(
        "ck_league_member_scoring_start_gameweek",
        "league_members",
        type_="check",
    )

    op.drop_column(
        "league_members",
        "scoring_start_gameweek",
    )

    op.drop_column(
        "league_members",
        "approved_at",
    )

    # 2. Remove league rules.
    op.drop_table("league_rules")

    # 3. Restore old league status enum.
    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status DROP DEFAULT
        """
    )

    op.execute(
        """
        CREATE TYPE league_status_old
        AS ENUM ('SETUP', 'ACTIVE', 'COMPLETED')
        """
    )

    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status
        TYPE league_status_old
        USING (
            CASE status::text
                WHEN 'DRAFT' THEN 'SETUP'
                WHEN 'ACTIVE' THEN 'ACTIVE'
            END
        )::league_status_old
        """
    )

    op.execute(
        """
        DROP TYPE league_status
        """
    )

    op.execute(
        """
        ALTER TYPE league_status_old
        RENAME TO league_status
        """
    )

    op.execute(
        """
        ALTER TABLE leagues
        ALTER COLUMN status
        SET DEFAULT 'SETUP'::league_status
        """
    )