import hashlib
import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)

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
    LeagueInvitationCreateResponse,
    LeagueInvitationPreviewResponse,
    LeagueInvitationResponse,
)
from app.services.league import (
    AlreadyLeagueMemberError,
    FPLAccountRequiredError,
    LeagueNotFoundError,
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


class InvitationExpiredError(Exception):
    pass


class InvitationRevokedError(Exception):
    pass


class InvitationOwnerRequiredError(Exception):
    pass


def _generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_invitation_token(
    token: str,
) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _validate_invitation(
    invitation: LeagueInvitation,
) -> None:
    now = datetime.now(timezone.utc)

    if invitation.revoked_at is not None:
        raise InvitationRevokedError

    if invitation.expires_at <= now:
        raise InvitationExpiredError


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


async def create_league_invitation(
    db: AsyncSession,
    *,
    slug: str,
    user_id: int,
    expires_in_days: int,
) -> LeagueInvitationCreateResponse:
    raw_token = _generate_invitation_token()

    token_hash = _hash_invitation_token(raw_token)

    now = datetime.now(timezone.utc)

    async with db.begin():
        league = await db.scalar(
            select(League)
            .where(
                League.slug == slug,
            )
            .with_for_update()
        )

        if league is None:
            raise LeagueNotFoundError

        await _require_invitation_owner(
            db=db,
            league_id=league.id,
            user_id=user_id,
        )

        invitation = LeagueInvitation(
            league_id=league.id,
            created_by_user_id=user_id,
            token_hash=token_hash,
            expires_at=(now + timedelta(days=expires_in_days)),
        )

        db.add(invitation)

        await db.flush()

        invitation_id = invitation.id
        expires_at = invitation.expires_at
        created_at = invitation.created_at
        league_slug = league.slug

    return LeagueInvitationCreateResponse(
        id=invitation_id,
        league_slug=league_slug,
        token=raw_token,
        expires_at=expires_at,
        created_at=created_at,
    )


async def preview_league_invitation(
    db: AsyncSession,
    *,
    token: str,
    user_id: int,
) -> LeagueInvitationPreviewResponse:
    token_hash = _hash_invitation_token(token)

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
            LeagueInvitation.token_hash == token_hash,
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
        expires_at=invitation.expires_at,
        already_member=(
            member is not None and member.status != LeagueMemberStatus.REJECTED
        ),
        membership_status=(member.status if member is not None else None),
    )


async def accept_league_invitation(
    db: AsyncSession,
    *,
    token: str,
    user_id: int,
) -> LeagueInvitationAcceptResponse:
    token_hash = _hash_invitation_token(token)
    membership_became_pending = False

    async with db.begin():
        invitation = await db.scalar(
            select(LeagueInvitation)
            .where(
                LeagueInvitation.token_hash == token_hash,
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


async def list_league_invitations(
    db: AsyncSession,
    *,
    slug: str,
    user_id: int,
) -> list[LeagueInvitationResponse]:
    league = await db.scalar(
        select(League).where(
            League.slug == slug,
        )
    )

    if league is None:
        raise LeagueNotFoundError

    await _require_invitation_owner(
        db=db,
        league_id=league.id,
        user_id=user_id,
    )

    acceptance_count = (
        select(func.count(LeagueInvitationAcceptance.id))
        .where(LeagueInvitationAcceptance.invitation_id == LeagueInvitation.id)
        .correlate(LeagueInvitation)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            LeagueInvitation,
            acceptance_count.label("acceptance_count"),
        )
        .where(
            LeagueInvitation.league_id == league.id,
        )
        .order_by(LeagueInvitation.created_at.desc())
    )

    now = datetime.now(timezone.utc)

    return [
        LeagueInvitationResponse(
            id=invitation.id,
            league_slug=league.slug,
            expires_at=(invitation.expires_at),
            revoked_at=(invitation.revoked_at),
            created_at=(invitation.created_at),
            acceptance_count=(count),
            active=(invitation.revoked_at is None and invitation.expires_at > now),
        )
        for invitation, count in result.all()
    ]


async def revoke_league_invitation(
    db: AsyncSession,
    *,
    slug: str,
    invitation_id: int,
    user_id: int,
) -> None:
    now = datetime.now(timezone.utc)

    async with db.begin():
        league = await db.scalar(
            select(League)
            .where(
                League.slug == slug,
            )
            .with_for_update()
        )

        if league is None:
            raise LeagueNotFoundError

        await _require_invitation_owner(
            db=db,
            league_id=league.id,
            user_id=user_id,
        )

        invitation = await db.scalar(
            select(LeagueInvitation)
            .where(
                LeagueInvitation.id == invitation_id,
                LeagueInvitation.league_id == league.id,
            )
            .with_for_update()
        )

        if invitation is None:
            raise InvitationNotFoundError

        # Idempotent revoke.
        if invitation.revoked_at is None:
            invitation.revoked_at = now
