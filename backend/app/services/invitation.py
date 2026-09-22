import secrets

from app.models.fpl_account import FPLAccount
from app.models.league import League
from app.models.league_invitation import (
    LeagueInvitation,
)
from app.models.league_invitation_acceptance import (
    LeagueInvitationAcceptance,
)
from app.models.league_member import (
    LeagueMember,
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.schemas.invitation import (
    LeagueInvitationAcceptResponse,
    LeagueInvitationLinkResponse,
    LeagueInvitationPreviewResponse,
)
from app.core.config import settings
from app.services.league import (
    AlreadyLeagueMemberError,
    FPLAccountRequiredError,
    LeagueNotFoundError,
    MAX_LEAGUE_MEMBERS,
    create_or_reopen_league_membership,
)
from app.services.notification import (
    notify_membership_pending,
)
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession


class InvitationNotFoundError(Exception):
    pass


class InvitationRevokedError(Exception):
    pass


class InvitationOwnerRequiredError(Exception):
    pass


def _generate_invitation_code() -> str:
    return secrets.token_urlsafe(32)


def _validate_invitation(
    invitation: LeagueInvitation,
) -> None:
    if invitation.revoked_at is not None:
        raise InvitationRevokedError


async def _require_invitation_owner(
    db: AsyncSession,
    *,
    league_id: int,
    user_id: int,
) -> LeagueMember:
    owner = await db.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == user_id,
            LeagueMember.role == LeagueMemberRole.OWNER,
            LeagueMember.status == LeagueMemberStatus.APPROVED,
        )
    )

    if owner is None:
        raise InvitationOwnerRequiredError

    return owner


def _invitation_link(code: str) -> str:
    return f"{settings.frontend_base_url.rstrip('/')}/invitations/{code}"


async def get_league_invitation_link(
    db: AsyncSession,
    *,
    slug: str,
    user_id: int,
) -> LeagueInvitationLinkResponse:
    league = await db.scalar(select(League).where(League.slug == slug))
    if league is None:
        raise LeagueNotFoundError

    await _require_invitation_owner(
        db=db, league_id=league.id, user_id=user_id
    )
    invitation = await db.scalar(
        select(LeagueInvitation).where(
            LeagueInvitation.league_id == league.id
        )
    )
    if invitation is None:
        raise InvitationNotFoundError

    return LeagueInvitationLinkResponse(
        league_slug=league.slug,
        invitation_url=_invitation_link(invitation.code),
    )


async def regenerate_league_invitation_link(
    db: AsyncSession,
    *,
    slug: str,
    user_id: int,
) -> LeagueInvitationLinkResponse:
    async with db.begin():
        league = await db.scalar(
            select(League).where(League.slug == slug).with_for_update()
        )
        if league is None:
            raise LeagueNotFoundError

        await _require_invitation_owner(
            db=db, league_id=league.id, user_id=user_id
        )
        invitation = await db.scalar(
            select(LeagueInvitation)
            .where(LeagueInvitation.league_id == league.id)
            .with_for_update()
        )
        if invitation is None:
            raise InvitationNotFoundError

        invitation.code = _generate_invitation_code()
        invitation.revoked_at = None
        code = invitation.code

    return LeagueInvitationLinkResponse(
        league_slug=slug,
        invitation_url=_invitation_link(code),
    )


async def preview_league_invitation(
    db: AsyncSession,
    *,
    token: str,
    user_id: int,
) -> LeagueInvitationPreviewResponse:
    result = await db.execute(
        select(
            LeagueInvitation,
            League,
        )
        .join(
            League,
            League.id == LeagueInvitation.league_id,
        )
        .where(
            LeagueInvitation.code == token,
        )
    )

    row = result.first()

    if row is None:
        raise InvitationNotFoundError

    invitation, league = row

    _validate_invitation(invitation)

    member = await db.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == user_id,
        )
    )

    return LeagueInvitationPreviewResponse(
        invitation_id=invitation.id,
        league_name=league.name,
        league_slug=league.slug,
        already_member=(
            member is not None and member.status != LeagueMemberStatus.REJECTED
        ),
        membership_status=(member.status if member is not None else None),
        league_full=(
            await db.scalar(
                select(func.count(LeagueMember.id)).where(
                    LeagueMember.league_id == league.id,
                    LeagueMember.status == LeagueMemberStatus.APPROVED,
                )
            )
            >= MAX_LEAGUE_MEMBERS
        ),
    )


async def accept_league_invitation(
    db: AsyncSession,
    *,
    token: str,
    user_id: int,
) -> LeagueInvitationAcceptResponse:
    membership_became_pending = False

    async with db.begin():
        invitation = await db.scalar(
            select(LeagueInvitation)
            .where(
                LeagueInvitation.code == token,
            )
            .with_for_update()
        )

        if invitation is None:
            raise InvitationNotFoundError

        _validate_invitation(invitation)

        # Locking the league serializes membership
        # creation / capacity checks.
        league = await db.scalar(
            select(League)
            .where(
                League.id == invitation.league_id,
            )
            .with_for_update()
        )

        if league is None:
            raise LeagueNotFoundError

        account = await db.scalar(
            select(FPLAccount).where(
                FPLAccount.user_id == user_id,
            )
        )

        if account is None:
            raise FPLAccountRequiredError

        acceptance = await db.scalar(
            select(LeagueInvitationAcceptance).where(
                LeagueInvitationAcceptance.invitation_id == invitation.id,
                LeagueInvitationAcceptance.user_id == user_id,
            )
        )

        existing_member = await db.scalar(
            select(LeagueMember)
            .where(
                LeagueMember.league_id == league.id,
                LeagueMember.user_id == user_id,
            )
            .with_for_update()
        )

        # Already accepted and still PENDING /
        # APPROVED: make retries idempotent.
        if (
            acceptance is not None
            and existing_member is not None
            and existing_member.status
            in {
                LeagueMemberStatus.PENDING,
                LeagueMemberStatus.APPROVED,
            }
        ):
            return LeagueInvitationAcceptResponse(
                invitation_id=(invitation.id),
                league_id=league.id,
                league_name=league.name,
                league_slug=league.slug,
                league_member_id=(existing_member.id),
                membership_status=(existing_member.status),
            )

        # User might already be a member because
        # they previously accepted another invite.
        #
        # Accepting this invite should not create a
        # second membership.
        if existing_member is not None and existing_member.status in {
            LeagueMemberStatus.PENDING,
            LeagueMemberStatus.APPROVED,
        }:
            member = existing_member

        else:
            try:
                member = await create_or_reopen_league_membership(
                    db=db,
                    league=league,
                    user_id=user_id,
                    fpl_entry_id=(account.fpl_entry_id),
                )
                membership_became_pending = True

            except AlreadyLeagueMemberError:
                # Defensive fallback. The row was
                # already locked/read above.
                member = await db.scalar(
                    select(LeagueMember).where(
                        LeagueMember.league_id == league.id,
                        LeagueMember.user_id == user_id,
                    )
                )

                if member is None:
                    raise

        if membership_became_pending:
            owner = await db.scalar(
                select(LeagueMember).where(
                    LeagueMember.league_id == league.id,
                    LeagueMember.role == LeagueMemberRole.OWNER,
                    LeagueMember.status
                    == LeagueMemberStatus.APPROVED,
                )
            )

            if owner is not None and owner.user_id is not None:
                await notify_membership_pending(
                    db=db,
                    owner_user_id=owner.user_id,
                    league_id=league.id,
                    league_slug=league.slug,
                    league_name=league.name,
                    member_user_id=user_id,
                    team_name=account.team_name,
                )

        if acceptance is None:
            acceptance = LeagueInvitationAcceptance(
                invitation_id=(invitation.id),
                user_id=user_id,
            )

            db.add(acceptance)

        await db.flush()

        invitation_id = invitation.id
        league_id = league.id
        league_name = league.name
        league_slug = league.slug

        member_id = member.id
        member_status = member.status

    return LeagueInvitationAcceptResponse(
        invitation_id=invitation_id,
        league_id=league_id,
        league_name=league_name,
        league_slug=league_slug,
        league_member_id=member_id,
        membership_status=member_status,
    )
