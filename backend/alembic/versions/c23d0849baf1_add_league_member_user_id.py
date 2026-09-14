"""Link league memberships to authenticated users after the development reset.

Revision ID: c23d0849baf1
Revises: 00fe846063be
"""

from alembic import op
import sqlalchemy as sa

revision = "c23d0849baf1"
down_revision = "00fe846063be"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("league_members", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_league_members_user_id_users",
        "league_members",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index("ix_league_members_user_id", "league_members", ["user_id"])
    op.create_unique_constraint(
        "uq_league_member_user", "league_members", ["league_id", "user_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_league_member_user", "league_members", type_="unique")
    op.drop_index("ix_league_members_user_id", table_name="league_members")
    op.drop_constraint("fk_league_members_user_id_users", "league_members", type_="foreignkey")
    op.drop_column("league_members", "user_id")
