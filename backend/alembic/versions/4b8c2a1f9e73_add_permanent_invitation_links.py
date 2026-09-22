"""add permanent invitation links

Revision ID: 4b8c2a1f9e73
Revises: 67a5beaf85e3
Create Date: 2026-09-22 18:45:00.000000
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4b8c2a1f9e73"
down_revision: Union[str, Sequence[str], None] = "67a5beaf85e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "league_invitations",
        sa.Column("code", sa.String(length=64), nullable=True),
    )

    connection = op.get_bind()
    leagues = connection.execute(
        sa.text(
            """
            SELECT l.id, lm.user_id
            FROM leagues AS l
            JOIN league_members AS lm
              ON lm.league_id = l.id
             AND lm.role = 'OWNER'
             AND lm.status = 'APPROVED'
            """
        )
    ).all()

    for league_id, owner_user_id in leagues:
        invitations = connection.execute(
            sa.text(
                """
                SELECT id
                FROM league_invitations
                WHERE league_id = :league_id
                ORDER BY created_at DESC, id DESC
                """
            ),
            {"league_id": league_id},
        ).scalars().all()
        code = secrets.token_urlsafe(32)

        if invitations:
            retained_id = invitations[0]
            connection.execute(
                sa.text(
                    """
                    UPDATE league_invitations
                    SET code = :code, revoked_at = NULL
                    WHERE id = :invitation_id
                    """
                ),
                {"code": code, "invitation_id": retained_id},
            )
            if len(invitations) > 1:
                connection.execute(
                    sa.text(
                        """
                        DELETE FROM league_invitations
                        WHERE league_id = :league_id AND id != :retained_id
                        """
                    ),
                    {"league_id": league_id, "retained_id": retained_id},
                )
        else:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO league_invitations
                        (league_id, created_by_user_id, token_hash,
                         expires_at, code)
                    VALUES
                        (:league_id, :owner_user_id, :token_hash,
                         :expires_at, :code)
                    """
                ),
                {
                    "league_id": league_id,
                    "owner_user_id": owner_user_id,
                    "token_hash": hashlib.sha256(code.encode()).hexdigest(),
                    "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
                    "code": code,
                },
            )

    op.alter_column("league_invitations", "code", nullable=False)
    op.create_index(
        "ix_league_invitations_code",
        "league_invitations",
        ["code"],
        unique=True,
    )
    op.create_unique_constraint(
        "uq_league_invitations_league_id",
        "league_invitations",
        ["league_id"],
    )
    op.drop_index(
        "ix_league_invitations_token_hash",
        table_name="league_invitations",
    )
    op.drop_index(
        "ix_league_invitations_expires_at",
        table_name="league_invitations",
    )
    op.drop_column("league_invitations", "token_hash")
    op.drop_column("league_invitations", "expires_at")


def downgrade() -> None:
    op.add_column(
        "league_invitations",
        sa.Column("token_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "league_invitations",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, code FROM league_invitations")
    ).all()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    for invitation_id, code in rows:
        connection.execute(
            sa.text(
                """
                UPDATE league_invitations
                SET token_hash = :token_hash, expires_at = :expires_at
                WHERE id = :invitation_id
                """
            ),
            {
                "token_hash": hashlib.sha256(code.encode()).hexdigest(),
                "expires_at": expires_at,
                "invitation_id": invitation_id,
            },
        )

    op.alter_column("league_invitations", "token_hash", nullable=False)
    op.alter_column("league_invitations", "expires_at", nullable=False)
    op.create_index(
        "ix_league_invitations_token_hash",
        "league_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_league_invitations_expires_at",
        "league_invitations",
        ["expires_at"],
        unique=False,
    )
    op.drop_constraint(
        "uq_league_invitations_league_id",
        "league_invitations",
        type_="unique",
    )
    op.drop_index("ix_league_invitations_code", table_name="league_invitations")
    op.drop_column("league_invitations", "code")
