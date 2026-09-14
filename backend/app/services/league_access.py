from app.models.league_member import (
    LeagueMember,
    LeagueMemberStatus,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class LeagueMembershipRequiredError(Exception):
    pass


class LeagueMembershipPendingError(Exception):
    pass


async def require_approved_league_member(
    db: AsyncSession,
    *,
    league_id: int,
    user_id: int,
) -> LeagueMember:
    member = await db.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == user_id,
        )
    )

    if member is None:
        raise LeagueMembershipRequiredError

    if member.status == LeagueMemberStatus.PENDING:
        raise LeagueMembershipPendingError

    if member.status != LeagueMemberStatus.APPROVED:
        raise LeagueMembershipRequiredError

    return member
