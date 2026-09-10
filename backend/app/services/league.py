from datetime import datetime, timezone

from app.models.league import League, LeagueStatus
from app.models.league_member import (
    LeagueMember,
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.models.league_rules import LeagueRules
from app.schemas.league import (
    LeagueCreate,
    LeagueDetailResponse,
    LeagueJoinRequest,
    LeagueMemberResponse,
    LeagueResponse,
    LeagueRulesResponse,
    LeagueStatusResponse,
    LeagueUpdate,
)
from app.services.fpl import (
    find_fpl_manager,
    get_current_gameweek,
)
from slugify import slugify
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

MAX_LEAGUE_MEMBERS = 20

class FPLTeamNotFoundError(Exception):
    pass


class DuplicateLeagueError(Exception):
    pass

class LeagueNotFoundError(Exception):
    pass

class LeagueRulesNotFoundError(Exception):
    pass


class LeagueFullError(Exception):
    pass


class AlreadyLeagueMemberError(Exception):
    pass


class LeagueMemberNotFoundError(Exception):
    pass


class LeagueOwnerRequiredError(Exception):
    pass


class InvalidMemberStatusError(Exception):
    pass


class CannotManageOwnerError(Exception):
    pass

class LeagueAlreadyActiveError(Exception):
    pass

class LeagueEditingClosedError(Exception):
    pass

async def create_league(
    db: AsyncSession,
    data: LeagueCreate,
) -> LeagueResponse:
    manager = await find_fpl_manager(data.fpl_entry_id)

    if manager is None:
        raise FPLTeamNotFoundError

    league_slug = slugify(data.name)

    league = League(
        name=data.name,
        slug=league_slug,
    )

    approved_at = datetime.now(timezone.utc)

    try:
        async with db.begin():
            existing_league = await db.scalar(
                select(League).where(
                    League.slug == league_slug,
                )
            )

            if existing_league is not None:
                raise DuplicateLeagueError

            db.add(league)

            await db.flush()

            rules = LeagueRules(
                league_id=league.id,
                start_gameweek=data.rules.start_gameweek,
                include_transfer_deductions=(
                    data.rules.include_transfer_deductions
                ),
                allowed_chips=[
                    chip.value
                    for chip in data.rules.allowed_chips
                ],
            )

            owner = LeagueMember(
                league_id=league.id,
                fpl_entry_id=data.fpl_entry_id,
                role=LeagueMemberRole.OWNER,
                status=LeagueMemberStatus.APPROVED,
                approved_at=approved_at,
                scoring_start_gameweek=(
                    data.rules.start_gameweek
                ),
            )

            db.add(rules)
            db.add(owner)

            await db.flush()

            await db.refresh(league)
            await db.refresh(rules)
            await db.refresh(owner)

    except IntegrityError as exc:
        raise DuplicateLeagueError from exc

    return LeagueResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        created_at=league.created_at,
        started_at=league.started_at,
        rules=LeagueRulesResponse(
            start_gameweek=rules.start_gameweek,
            include_transfer_deductions=rules.include_transfer_deductions,
            allowed_chips=rules.allowed_chips
        ),
        owner=_member_response(owner),
    )

async def get_league(
    db: AsyncSession,
    slug: str,
) -> LeagueDetailResponse:
    league = await db.scalar(
        select(League).where(
            League.slug == slug,
        )
    )

    if league is None:
        raise LeagueNotFoundError

    rules = await _get_league_rules(
        db=db,
        league_id=league.id,
    )

    members_result = await db.execute(
        select(LeagueMember)
        .where(
            LeagueMember.league_id == league.id,
        )
        .order_by(
            LeagueMember.joined_at.asc(),
        )
    )

    members = members_result.scalars().all()

    return LeagueDetailResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        created_at=league.created_at,
        started_at=league.started_at,
        rules=LeagueRulesResponse(
            start_gameweek=rules.start_gameweek,
            include_transfer_deductions=(
                rules.include_transfer_deductions
            ),
            allowed_chips=rules.allowed_chips,
        ),
        members=[
            _member_response(member)
            for member in members
        ],
    )

async def _get_league_for_update(
    db: AsyncSession,
    slug: str,
) -> League:
    league = await db.scalar(
        select(League)
        .where(League.slug == slug)
        .with_for_update()
    )

    if league is None:
        raise LeagueNotFoundError

    return league

async def _get_league_rules(
    db: AsyncSession,
    league_id: int,
) -> LeagueRules:
    rules = await db.scalar(
        select(LeagueRules).where(
            LeagueRules.league_id == league_id,
        )
    )

    if rules is None:
        raise LeagueRulesNotFoundError

    return rules

async def _require_owner(
    db: AsyncSession,
    league_id: int,
    owner_fpl_entry_id: int,
) -> LeagueMember:
    owner = await db.scalar(
        select(LeagueMember).where(
            LeagueMember.league_id == league_id,
            LeagueMember.fpl_entry_id
            == owner_fpl_entry_id,
            LeagueMember.role
            == LeagueMemberRole.OWNER,
            LeagueMember.status
            == LeagueMemberStatus.APPROVED,
        )
    )

    if owner is None:
        raise LeagueOwnerRequiredError

    return owner

def _member_response(
    member: LeagueMember,
) -> LeagueMemberResponse:
    return LeagueMemberResponse(
        id=member.id,
        fpl_entry_id=member.fpl_entry_id,
        role=member.role,
        status=member.status,
        joined_at=member.joined_at,
        approved_at=member.approved_at,
        scoring_start_gameweek=(
            member.scoring_start_gameweek
        ),
    )

async def join_league(
    db: AsyncSession,
    slug: str,
    data: LeagueJoinRequest,
) -> LeagueMemberResponse:
    manager = await find_fpl_manager(
        data.fpl_entry_id
    )

    if manager is None:
        raise FPLTeamNotFoundError

    try:
        async with db.begin():
            league = await _get_league_for_update(
                db=db,
                slug=slug,
            )

            existing_member = await db.scalar(
                select(LeagueMember).where(
                    LeagueMember.league_id
                    == league.id,
                    LeagueMember.fpl_entry_id
                    == data.fpl_entry_id,
                )
            )

            if existing_member is not None:
                if (
                    existing_member.status
                    == LeagueMemberStatus.REJECTED
                ):
                    approved_count = await db.scalar(
                        select(
                            func.count(
                                LeagueMember.id
                            )
                        ).where(
                            LeagueMember.league_id
                            == league.id,
                            LeagueMember.status
                            == LeagueMemberStatus.APPROVED,
                        )
                    )

                    if (
                        approved_count
                        >= MAX_LEAGUE_MEMBERS
                    ):
                        raise LeagueFullError

                    existing_member.status = (
                        LeagueMemberStatus.PENDING
                    )
                    existing_member.approved_at = None
                    existing_member.scoring_start_gameweek = (
                        None
                    )
                    existing_member.joined_at = (
                        datetime.now(timezone.utc)
                    )

                    await db.flush()
                    await db.refresh(existing_member)

                    return _member_response(
                        existing_member
                    )

                raise AlreadyLeagueMemberError

            approved_count = await db.scalar(
                select(
                    func.count(LeagueMember.id)
                ).where(
                    LeagueMember.league_id == league.id,
                    LeagueMember.status
                    == LeagueMemberStatus.APPROVED,
                )
            )

            if approved_count >= MAX_LEAGUE_MEMBERS:
                raise LeagueFullError

            member = LeagueMember(
                league_id=league.id,
                fpl_entry_id=data.fpl_entry_id,
                role=LeagueMemberRole.MEMBER,
                status=LeagueMemberStatus.PENDING,
            )

            db.add(member)

            await db.flush()
            await db.refresh(member)

    except IntegrityError as exc:
        raise AlreadyLeagueMemberError from exc

    return _member_response(member)

async def approve_league_member(
    db: AsyncSession,
    slug: str,
    member_id: int,
    owner_fpl_entry_id: int,
) -> LeagueMemberResponse:
    current_gameweek = await get_current_gameweek()

    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            owner_fpl_entry_id=owner_fpl_entry_id,
        )

        rules = await _get_league_rules(
            db=db,
            league_id=league.id,
        )

        member = await db.scalar(
            select(LeagueMember).where(
                LeagueMember.id == member_id,
                LeagueMember.league_id == league.id,
            )
        )

        if member is None:
            raise LeagueMemberNotFoundError

        if member.role == LeagueMemberRole.OWNER:
            raise CannotManageOwnerError

        if (
            member.status
            != LeagueMemberStatus.PENDING
        ):
            raise InvalidMemberStatusError

        approved_count = await db.scalar(
            select(
                func.count(LeagueMember.id)
            ).where(
                LeagueMember.league_id == league.id,
                LeagueMember.status
                == LeagueMemberStatus.APPROVED,
            )
        )

        if approved_count >= MAX_LEAGUE_MEMBERS:
            raise LeagueFullError

        if league.status == LeagueStatus.DRAFT:
            scoring_start_gameweek = (
                rules.start_gameweek
            )

        else:
            scoring_start_gameweek = max(
                rules.start_gameweek,
                current_gameweek,
            )

        member.status = LeagueMemberStatus.APPROVED
        member.approved_at = datetime.now(
            timezone.utc
        )
        member.scoring_start_gameweek = (
            scoring_start_gameweek
        )

        await db.flush()
        await db.refresh(member)

    return _member_response(member)

async def reject_league_member(
    db: AsyncSession,
    slug: str,
    member_id: int,
    owner_fpl_entry_id: int,
) -> LeagueMemberResponse:
    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            owner_fpl_entry_id=owner_fpl_entry_id,
        )

        member = await db.scalar(
            select(LeagueMember).where(
                LeagueMember.id == member_id,
                LeagueMember.league_id == league.id,
            )
        )

        if member is None:
            raise LeagueMemberNotFoundError

        if member.role == LeagueMemberRole.OWNER:
            raise CannotManageOwnerError

        if (
            member.status
            != LeagueMemberStatus.PENDING
        ):
            raise InvalidMemberStatusError

        member.status = LeagueMemberStatus.REJECTED
        member.approved_at = None
        member.scoring_start_gameweek = None

        await db.flush()
        await db.refresh(member)

    return _member_response(member)

async def activate_league(
    db: AsyncSession,
    slug: str,
    owner_fpl_entry_id: int,
) -> LeagueStatusResponse:
    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            owner_fpl_entry_id=owner_fpl_entry_id,
        )

        if league.status == LeagueStatus.ACTIVE:
            raise LeagueAlreadyActiveError

        league.status = LeagueStatus.ACTIVE
        league.started_at = datetime.now(
            timezone.utc
        )

        await db.flush()
        await db.refresh(league)

    return LeagueStatusResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        started_at=league.started_at,
    )

async def update_league(
    db: AsyncSession,
    slug: str,
    data: LeagueUpdate,
) -> LeagueDetailResponse:
    try:
        async with db.begin():
            league = await _get_league_for_update(
                db=db,
                slug=slug,
            )

            await _require_owner(
                db=db,
                league_id=league.id,
                owner_fpl_entry_id=(
                    data.owner_fpl_entry_id
                ),
            )

            if league.status != LeagueStatus.DRAFT:
                raise LeagueEditingClosedError

            rules = await _get_league_rules(
                db=db,
                league_id=league.id,
            )

            # Update league name and therefore its public slug.
            if data.name is not None:
                new_slug = slugify(data.name)

                if new_slug != league.slug:
                    existing_league = await db.scalar(
                        select(League).where(
                            League.slug == new_slug,
                            League.id != league.id,
                        )
                    )

                    if existing_league is not None:
                        raise DuplicateLeagueError

                league.name = data.name
                league.slug = new_slug

            # Update competition rules.
            if data.rules is not None:
                old_start_gameweek = (
                    rules.start_gameweek
                )

                if (
                    data.rules.start_gameweek
                    is not None
                ):
                    rules.start_gameweek = (
                        data.rules.start_gameweek
                    )

                if (
                    data.rules.include_transfer_deductions
                    is not None
                ):
                    rules.include_transfer_deductions = (
                        data.rules
                        .include_transfer_deductions
                    )

                if data.rules.allowed_chips is not None:
                    rules.allowed_chips = [
                        chip.value
                        for chip
                        in data.rules.allowed_chips
                    ]

                # Everyone approved during DRAFT starts
                # from the league's configured start GW.
                if (
                    rules.start_gameweek
                    != old_start_gameweek
                ):
                    await db.execute(
                        update(LeagueMember)
                        .where(
                            LeagueMember.league_id
                            == league.id,
                            LeagueMember.status
                            == LeagueMemberStatus.APPROVED,
                        )
                        .values(
                            scoring_start_gameweek=(
                                rules.start_gameweek
                            )
                        )
                    )

            await db.flush()

            await db.refresh(league)
            await db.refresh(rules)

            members_result = await db.execute(
                select(LeagueMember)
                .where(
                    LeagueMember.league_id
                    == league.id,
                )
                .order_by(
                    LeagueMember.joined_at.asc(),
                )
            )

            members = members_result.scalars().all()

    except IntegrityError as exc:
        raise DuplicateLeagueError from exc

    return LeagueDetailResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        created_at=league.created_at,
        started_at=league.started_at,
        rules=LeagueRulesResponse(
            start_gameweek=rules.start_gameweek,
            include_transfer_deductions=(
                rules.include_transfer_deductions
            ),
            allowed_chips=rules.allowed_chips,
        ),
        members=[
            _member_response(member)
            for member in members
        ],
    )
