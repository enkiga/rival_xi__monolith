"""Cascade user deletion to league memberships.

Revision ID: d54b17ac9032
Revises: c23d0849baf1
"""

from alembic import op

revision = "d54b17ac9032"
down_revision = "c23d0849baf1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_league_members_user_id_users", "league_members", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_league_members_user_id_users",
        "league_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_league_members_user_id_users", "league_members", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_league_members_user_id_users",
        "league_members",
        "users",
        ["user_id"],
        ["id"],
    )
