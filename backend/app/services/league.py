import secrets
from datetime import datetime, timezone

from app.models.fpl_account import FPLAccount
from app.models.gameweek_result import GameweekResult
from app.models.league import League, LeagueStatus
from app.models.league_invitation import LeagueInvitation
from app.models.league_member import (
    LeagueMember,
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.models.league_rules import LeagueRules
from app.schemas.league import (
    LeagueCreate,
    LeagueDetailResponse,
    LeagueDetailMemberResponse,
    LeagueListItemResponse,
    LeagueListResponse,
    LeagueMemberResponse,
    LeagueResponse,
    LeagueRulesResponse,
    LeagueStatusResponse,
    LeagueUpdate,
)
from app.services.fpl import (
    get_current_gameweek,
)
from app.services.league_access import (
    require_approved_league_member,
)
from app.services.notification import (
    deliver_notification_email,
    notify_league_rules_changed,
    notify_membership_approved,
    notify_membership_rejected,
)
from slugify import slugify
from sqlalchemy import case, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

MAX_LEAGUE_MEMBERS = 20


class FPLAccountRequiredError(Exception):
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
    *,
    user_id: int,
) -> LeagueResponse:
    league_slug = slugify(data.name)

    league = League(
        name=data.name,
        slug=league_slug,
    )

    approved_at = datetime.now(timezone.utc)

    try:
        async with db.begin():
            account = await _get_user_fpl_account(db, user_id)

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
                include_transfer_deductions=(data.rules.include_transfer_deductions),
                allowed_chips=[chip.value for chip in data.rules.allowed_chips],
            )

            owner = LeagueMember(
                league_id=league.id,
                user_id=user_id,
                fpl_entry_id=account.fpl_entry_id,
                role=LeagueMemberRole.OWNER,
                status=LeagueMemberStatus.APPROVED,
                approved_at=approved_at,
                scoring_start_gameweek=(data.rules.start_gameweek),
            )

            db.add(rules)
            db.add(owner)
            db.add(
                LeagueInvitation(
                    league_id=league.id,
                    created_by_user_id=user_id,
                    code=secrets.token_urlsafe(32),
                )
            )

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
            allowed_chips=rules.allowed_chips,
        ),
        owner=_member_response(owner),
    )


async def get_league(
    db: AsyncSession,
    slug: str,
    *,
    user_id: int,
) -> LeagueDetailResponse:
    league = await db.scalar(
        select(League).where(
            League.slug == slug,
        )
    )

    if league is None:
        raise LeagueNotFoundError

    viewer = await require_approved_league_member(
        db=db,
        league_id=league.id,
        user_id=user_id,
    )

    rules = await _get_league_rules(
        db=db,
        league_id=league.id,
    )

    members_query = (
        select(LeagueMember, FPLAccount)
        .join(
            FPLAccount,
            FPLAccount.user_id == LeagueMember.user_id,
        )
        .where(
            LeagueMember.league_id == league.id,
        )
        .order_by(
            LeagueMember.joined_at.asc(),
        )
    )

    if viewer.role != LeagueMemberRole.OWNER:
        members_query = members_query.where(
            LeagueMember.status
            == LeagueMemberStatus.APPROVED,
        )

    members_result = await db.execute(members_query)

    members = members_result.all()
    current_gameweek = await get_current_gameweek()

    return LeagueDetailResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        created_at=league.created_at,
        started_at=league.started_at,
        current_gameweek=current_gameweek,
        rules=LeagueRulesResponse(
            start_gameweek=rules.start_gameweek,
            include_transfer_deductions=(rules.include_transfer_deductions),
            allowed_chips=rules.allowed_chips,
        ),
        members=[
            _detail_member_response(member, account)
            for member, account in members
        ],
    )


async def get_user_leagues(
    db: AsyncSession,
    *,
    user_id: int,
    page: int,
    page_size: int,
    search: str | None,
    sort_by: str,
    sort_order: str,
) -> LeagueListResponse:
    membership = aliased(LeagueMember)
    owner = aliased(LeagueMember)
    approved_member_count = (
        select(func.count(LeagueMember.id))
        .where(
            LeagueMember.league_id == League.id,
            LeagueMember.status == LeagueMemberStatus.APPROVED,
        )
        .correlate(League)
        .scalar_subquery()
    )

    filters = [
        membership.user_id == user_id,
        membership.status.in_(
            (
                LeagueMemberStatus.APPROVED,
                LeagueMemberStatus.PENDING,
            )
        ),
    ]

    normalized_search = search.strip() if search else None
    if normalized_search:
        filters.append(League.name.ilike(f"%{normalized_search}%"))

    total = await db.scalar(
        select(func.count(League.id))
        .join(
            membership,
            membership.league_id == League.id,
        )
        .where(*filters)
    )

    sort_column = League.name if sort_by == "name" else League.created_at
    ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    tie_breaker = League.id.asc() if sort_order == "asc" else League.id.desc()

    result = await db.execute(
        select(
            League,
            owner,
            membership,
            approved_member_count.label("member_count"),
        )
        .join(
            membership,
            membership.league_id == League.id,
        )
        .join(
            owner,
            (owner.league_id == League.id)
            & (owner.role == LeagueMemberRole.OWNER)
            & (owner.status == LeagueMemberStatus.APPROVED),
        )
        .where(*filters)
        .order_by(ordering, tie_breaker)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )

    rows = result.all()
    total_count = total or 0

    ranked_league_members = {
        league.id: viewer.id
        for league, _, viewer, _ in rows
        if league.status == LeagueStatus.ACTIVE
        and viewer.status == LeagueMemberStatus.APPROVED
    }
    last_gameweeks: dict[int, int] = {}
    ranks: dict[int, int] = {}

    if ranked_league_members:
        latest_gameweeks = (
            select(
                GameweekResult.league_id.label("league_id"),
                func.max(GameweekResult.gameweek).label("gameweek"),
            )
            .where(GameweekResult.league_id.in_(ranked_league_members))
            .group_by(GameweekResult.league_id)
            .subquery()
        )
        ranked_results = (
            select(
                GameweekResult.league_id.label("league_id"),
                GameweekResult.league_member_id.label("league_member_id"),
                func.rank()
                .over(
                    partition_by=GameweekResult.league_id,
                    order_by=(
                        GameweekResult.scoreboard_points.desc(),
                        case(
                            (GameweekResult.chip_used.is_not(None), 1),
                            else_=0,
                        ).asc(),
                        GameweekResult.transfer_deduction.asc(),
                    ),
                )
                .label("rank"),
            )
            .join(
                latest_gameweeks,
                (latest_gameweeks.c.league_id == GameweekResult.league_id)
                & (latest_gameweeks.c.gameweek == GameweekResult.gameweek),
            )
            .where(GameweekResult.eligible.is_(True))
            .subquery()
        )
        standings_result = await db.execute(
            select(
                latest_gameweeks.c.league_id,
                latest_gameweeks.c.gameweek,
                ranked_results.c.league_member_id,
                ranked_results.c.rank,
            ).outerjoin(
                ranked_results,
                ranked_results.c.league_id == latest_gameweeks.c.league_id,
            )
        )

        for standing in standings_result.all():
            last_gameweeks[standing.league_id] = standing.gameweek
            if (
                standing.league_member_id
                == ranked_league_members[standing.league_id]
            ):
                ranks[standing.league_id] = standing.rank

    return LeagueListResponse(
        items=[
            LeagueListItemResponse(
                name=league.name,
                slug=league.slug,
                status=league.status,
                owner=_member_response(league_owner),
                member_count=member_count,
                max_member_count=MAX_LEAGUE_MEMBERS,
                last_scored_gameweek=last_gameweeks.get(league.id),
                rank=ranks.get(league.id),
            )
            for league, league_owner, _, member_count in rows
        ],
        total=total_count,
        page=page,
        page_size=page_size,
        pages=(total_count + page_size - 1) // page_size,
    )


async def _get_league_for_update(
    db: AsyncSession,
    slug: str,
) -> League:
    league = await db.scalar(
        select(League).where(League.slug == slug).with_for_update()
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
        scoring_start_gameweek=(member.scoring_start_gameweek),
    )


def _detail_member_response(
    member: LeagueMember,
    account: FPLAccount,
) -> LeagueDetailMemberResponse:
    return LeagueDetailMemberResponse(
        **_member_response(member).model_dump(),
        team_name=account.team_name,
        manager_name=account.manager_name,
    )


async def _get_user_fpl_account(
    db: AsyncSession,
    user_id: int,
) -> FPLAccount:
    account = await db.scalar(
        select(FPLAccount).where(
            FPLAccount.user_id == user_id,
        )
    )

    if account is None:
        raise FPLAccountRequiredError

    return account


async def create_or_reopen_league_membership(
    db: AsyncSession,
    *,
    league: League,
    user_id: int,
    fpl_entry_id: int,
) -> LeagueMember:
    existing = await db.scalar(
        select(LeagueMember)
        .where(
            LeagueMember.league_id == league.id,
            LeagueMember.user_id == user_id,
        )
        .with_for_update()
    )

    approved_count = await db.scalar(
        select(func.count(LeagueMember.id)).where(
            LeagueMember.league_id == league.id,
            LeagueMember.status == LeagueMemberStatus.APPROVED,
        )
    )

    if approved_count is not None and approved_count >= MAX_LEAGUE_MEMBERS:
        raise LeagueFullError

    if existing is not None:
        if existing.role == LeagueMemberRole.OWNER:
            raise AlreadyLeagueMemberError

        if existing.status == LeagueMemberStatus.REJECTED:
            existing.status = LeagueMemberStatus.PENDING
            existing.fpl_entry_id = fpl_entry_id
            existing.approved_at = None
            existing.scoring_start_gameweek = None
            existing.joined_at = datetime.now(timezone.utc)

            await db.flush()

            return existing

        raise AlreadyLeagueMemberError

    member = LeagueMember(
        league_id=league.id,
        user_id=user_id,
        fpl_entry_id=fpl_entry_id,
        role=LeagueMemberRole.MEMBER,
        status=LeagueMemberStatus.PENDING,
    )

    db.add(member)

    await db.flush()

    return member


async def approve_league_member(
    db: AsyncSession,
    slug: str,
    member_id: int,
    owner_user_id: int,
) -> LeagueMemberResponse:
    current_gameweek = await get_current_gameweek()
    notification_id: int | None = None

    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            user_id=owner_user_id,
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

        if member.status != LeagueMemberStatus.PENDING:
            raise InvalidMemberStatusError

        approved_count = await db.scalar(
            select(func.count(LeagueMember.id)).where(
                LeagueMember.league_id == league.id,
                LeagueMember.status == LeagueMemberStatus.APPROVED,
            )
        )

        if approved_count >= MAX_LEAGUE_MEMBERS:
            raise LeagueFullError

        if league.status == LeagueStatus.DRAFT:
            scoring_start_gameweek = rules.start_gameweek

        else:
            scoring_start_gameweek = max(
                rules.start_gameweek,
                current_gameweek,
            )

        member.status = LeagueMemberStatus.APPROVED
        member.approved_at = datetime.now(timezone.utc)
        member.scoring_start_gameweek = scoring_start_gameweek

        if member.user_id is not None:
            notification = await notify_membership_approved(
                db=db,
                user_id=member.user_id,
                league_id=league.id,
                league_slug=league.slug,
                league_name=league.name,
            )
            notification_id = notification.id

        await db.flush()
        await db.refresh(member)

    if notification_id is not None:
        await deliver_notification_email(notification_id)

    return _member_response(member)


async def reject_league_member(
    db: AsyncSession,
    slug: str,
    member_id: int,
    owner_user_id: int,
) -> LeagueMemberResponse:
    notification_id: int | None = None

    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            user_id=owner_user_id,
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

        if member.status != LeagueMemberStatus.PENDING:
            raise InvalidMemberStatusError

        member.status = LeagueMemberStatus.REJECTED
        member.approved_at = None
        member.scoring_start_gameweek = None

        if member.user_id is not None:
            notification = await notify_membership_rejected(
                db=db,
                user_id=member.user_id,
                league_id=league.id,
                league_slug=league.slug,
                league_name=league.name,
            )
            notification_id = notification.id

        await db.flush()
        await db.refresh(member)

    if notification_id is not None:
        await deliver_notification_email(notification_id)

    return _member_response(member)


async def activate_league(
    db: AsyncSession,
    slug: str,
    owner_user_id: int,
) -> LeagueStatusResponse:
    async with db.begin():
        league = await _get_league_for_update(
            db=db,
            slug=slug,
        )

        await _require_owner(
            db=db,
            league_id=league.id,
            user_id=owner_user_id,
        )

        if league.status == LeagueStatus.ACTIVE:
            raise LeagueAlreadyActiveError

        league.status = LeagueStatus.ACTIVE
        league.started_at = datetime.now(timezone.utc)

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
    *,
    owner_user_id: int,
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
                user_id=owner_user_id,
            )

            if league.status != LeagueStatus.DRAFT:
                raise LeagueEditingClosedError

            rules = await _get_league_rules(
                db=db,
                league_id=league.id,
            )
            changed_rule_fields: list[str] = []

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
                old_start_gameweek = rules.start_gameweek

                if (
                    data.rules.start_gameweek is not None
                    and data.rules.start_gameweek
                    != rules.start_gameweek
                ):
                    changed_rule_fields.append("start_gameweek")
                    rules.start_gameweek = data.rules.start_gameweek

                if (
                    data.rules.include_transfer_deductions is not None
                    and data.rules.include_transfer_deductions
                    != rules.include_transfer_deductions
                ):
                    changed_rule_fields.append(
                        "include_transfer_deductions"
                    )
                    rules.include_transfer_deductions = (
                        data.rules.include_transfer_deductions
                    )

                if data.rules.allowed_chips is not None:
                    allowed_chips = [
                        chip.value for chip in data.rules.allowed_chips
                    ]

                    if allowed_chips != rules.allowed_chips:
                        changed_rule_fields.append("allowed_chips")
                        rules.allowed_chips = allowed_chips

                # Everyone approved during DRAFT starts
                # from the league's configured start GW.
                if rules.start_gameweek != old_start_gameweek:
                    await db.execute(
                        update(LeagueMember)
                        .where(
                            LeagueMember.league_id == league.id,
                            LeagueMember.status == LeagueMemberStatus.APPROVED,
                        )
                        .values(scoring_start_gameweek=(rules.start_gameweek))
                    )

            if changed_rule_fields:
                recipient_result = await db.execute(
                    select(LeagueMember.user_id).where(
                        LeagueMember.league_id == league.id,
                        LeagueMember.status
                        == LeagueMemberStatus.APPROVED,
                        LeagueMember.user_id.is_not(None),
                        LeagueMember.user_id != owner_user_id,
                    )
                )

                recipient_user_ids = recipient_result.scalars().all()

                for recipient_user_id in recipient_user_ids:
                    await notify_league_rules_changed(
                        db=db,
                        user_id=recipient_user_id,
                        league_id=league.id,
                        league_slug=league.slug,
                        league_name=league.name,
                        changed_fields=changed_rule_fields,
                    )

            await db.flush()

            await db.refresh(league)
            await db.refresh(rules)

            members_result = await db.execute(
                select(LeagueMember, FPLAccount)
                .join(
                    FPLAccount,
                    FPLAccount.user_id == LeagueMember.user_id,
                )
                .where(
                    LeagueMember.league_id == league.id,
                )
                .order_by(
                    LeagueMember.joined_at.asc(),
                )
            )

            members = members_result.all()

    except IntegrityError as exc:
        raise DuplicateLeagueError from exc

    current_gameweek = await get_current_gameweek()

    return LeagueDetailResponse(
        id=league.id,
        name=league.name,
        slug=league.slug,
        status=league.status,
        created_at=league.created_at,
        started_at=league.started_at,
        current_gameweek=current_gameweek,
        rules=LeagueRulesResponse(
            start_gameweek=rules.start_gameweek,
            include_transfer_deductions=(rules.include_transfer_deductions),
            allowed_chips=rules.allowed_chips,
        ),
        members=[
            _detail_member_response(member, account)
            for member, account in members
        ],
    )
