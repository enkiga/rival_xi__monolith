from datetime import datetime, timezone

from app.core.cache import (
    get_cached_model,
    set_cached_model,
)
from app.integrations.fpl.client import (
    get_bootstrap_static,
    get_cached_bootstrap_static,
    get_event_live,
)
from app.models.fpl_account import FPLAccount
from app.models.gameweek_pick import GameweekPick
from app.models.gameweek_result import (
    GameweekIneligibilityReason,
    GameweekResult,
    GameweekResultStatus,
)
from app.models.league import (
    League,
    LeagueStatus,
)
from app.models.league_member import (
    LeagueMember,
    LeagueMemberStatus,
)
from app.models.league_rules import (
    FPLChip,
    LeagueRules,
)
from app.schemas.fpl import FPLGameweekResponse
from app.schemas.gameweek import (
    GameweekPickResponse,
    GameweekStandingResponse,
    GameweekSyncMemberResponse,
    LeagueGameweekResponse,
    LeagueGameweekSyncResponse,
    MemberGameweekResponse,
    RivalxiGameweekScore,
)
from app.services.fpl import (
    FPLGameweekNotFoundError,
    FPLPlayerNotFoundError,
    FPLPlayerPosition,
    UnsupportedFPLChipError,
    UnsupportedFPLPositionError,
    get_fpl_gameweek,
)
from app.services.gameweek_cache import (
    gameweek_response_ttl,
    invalidate_gameweek_cache,
    member_gameweek_cache_key,
    standings_cache_key,
)
from app.services.league_access import (
    require_approved_league_member,
)
from app.services.notification import (
    notify_gameweek_winner,
)
from app.services.league import LeagueOwnerRequiredError, _require_owner
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

CHIP_LABELS: dict[str, str] = {
    "WILDCARD": "Wildcard",
    "FREE_HIT": "Free Hit",
    "BENCH_BOOST": "Bench Boost",
    "TRIPLE_CAPTAIN": "Triple Captain",
}


class GameweekEventNotFoundError(Exception):
    pass


class FutureGameweekError(Exception):
    pass


class GameweekBeforeLeagueStartError(Exception):
    pass


class LeagueNotActiveError(Exception):
    pass


class GameweekLeagueNotFoundError(Exception):
    pass


class GameweekLeagueRulesNotFoundError(Exception):
    pass


class GameweekSyncOwnerRequiredError(Exception):
    pass


class GameweekSyncDataError(Exception):
    pass


class GameweekResultsNotFoundError(Exception):
    pass


class GameweekMemberResultNotFoundError(Exception):
    pass


def calculate_gameweek_score(
    fpl_gameweek: FPLGameweekResponse,
    rules: LeagueRules,
) -> RivalxiGameweekScore:
    allowed_chips = {
        chip.value if isinstance(chip, FPLChip) else chip
        for chip in rules.allowed_chips
    }

    chip_used = fpl_gameweek.chip_used

    chip_allowed = chip_used is None or chip_used.value in allowed_chips

    eligible = chip_allowed

    ineligibility_reason = None

    if not chip_allowed:
        ineligibility_reason = GameweekIneligibilityReason.PROHIBITED_CHIP

    if rules.include_transfer_deductions:
        scoreboard_points = fpl_gameweek.net_points
    else:
        scoreboard_points = fpl_gameweek.gross_points

    return RivalxiGameweekScore(
        entry_id=fpl_gameweek.entry_id,
        gameweek=fpl_gameweek.gameweek,
        gross_points=fpl_gameweek.gross_points,
        transfer_deduction=(fpl_gameweek.transfer_deduction),
        net_points=fpl_gameweek.net_points,
        scoreboard_points=scoreboard_points,
        transfers_made=(fpl_gameweek.transfers_made),
        points_on_bench=(fpl_gameweek.points_on_bench),
        chip_used=chip_used,
        chip_allowed=chip_allowed,
        eligible=eligible,
        ineligibility_reason=(ineligibility_reason),
    )


def _get_gameweek_event(
    bootstrap: dict,
    gameweek: int,
) -> dict:
    for event in bootstrap.get(
        "events",
        [],
    ):
        if event.get("id") == gameweek:
            return event

    raise GameweekEventNotFoundError


def validate_gameweek_started(
    event: dict,
) -> None:
    deadline_time = event.get("deadline_time")

    if deadline_time is None:
        raise GameweekEventNotFoundError

    deadline = datetime.fromisoformat(
        deadline_time.replace(
            "Z",
            "+00:00",
        )
    )

    if datetime.now(timezone.utc) < deadline:
        raise FutureGameweekError


def _get_result_status(
    event: dict,
) -> GameweekResultStatus:
    finished = event.get(
        "finished",
        False,
    )

    data_checked = event.get(
        "data_checked",
        True,
    )

    if finished and data_checked:
        return GameweekResultStatus.FINAL

    return GameweekResultStatus.LIVE


async def sync_league_gameweek(
    db: AsyncSession,
    slug: str,
    gameweek: int,
    *,
    bootstrap: dict | None = None,
    live_data: dict | None = None,
    fpl_gameweek_cache: dict[
        int,
        FPLGameweekResponse,
    ]
    | None = None,
) -> LeagueGameweekSyncResponse:
    if bootstrap is None:
        bootstrap = await get_bootstrap_static()

    event = _get_gameweek_event(
        bootstrap=bootstrap,
        gameweek=gameweek,
    )

    validate_gameweek_started(event)

    result_status = _get_result_status(event)

    if fpl_gameweek_cache is None:
        fpl_gameweek_cache = {}

    async with db.begin():
        league = await db.scalar(
            select(League).where(
                League.slug == slug,
            )
        )

        if league is None:
            raise GameweekLeagueNotFoundError

        if league.status != LeagueStatus.ACTIVE:
            raise LeagueNotActiveError

        rules = await db.scalar(
            select(LeagueRules).where(
                LeagueRules.league_id == league.id,
            )
        )

        if rules is None:
            raise GameweekLeagueRulesNotFoundError

        if gameweek < rules.start_gameweek:
            raise GameweekBeforeLeagueStartError

        members_result = await db.execute(
            select(
                LeagueMember.id,
                LeagueMember.fpl_entry_id,
            ).where(
                LeagueMember.league_id == league.id,
                LeagueMember.status == LeagueMemberStatus.APPROVED,
                LeagueMember.scoring_start_gameweek.is_not(None),
                LeagueMember.scoring_start_gameweek <= gameweek,
            )
        )

        member_snapshots = [
            (
                row.id,
                row.fpl_entry_id,
            )
            for row in members_result.all()
        ]

        league_id = league.id
        league_slug = league.slug

    if live_data is None:
        live_data = await get_event_live(
            gameweek=gameweek,
        )

    prepared_results: list[
        tuple[
            int,
            FPLGameweekResponse,
            RivalxiGameweekScore,
        ]
    ] = []

    for (
        league_member_id,
        fpl_entry_id,
    ) in member_snapshots:
        try:
            fpl_gameweek = fpl_gameweek_cache.get(fpl_entry_id)

            if fpl_gameweek is None:
                fpl_gameweek = await get_fpl_gameweek(
                    entry_id=fpl_entry_id,
                    gameweek=gameweek,
                    bootstrap=bootstrap,
                    live_data=live_data,
                )

                fpl_gameweek_cache[fpl_entry_id] = fpl_gameweek

        except (
            FPLGameweekNotFoundError,
            FPLPlayerNotFoundError,
            UnsupportedFPLChipError,
            UnsupportedFPLPositionError,
        ) as exc:
            raise GameweekSyncDataError(fpl_entry_id) from exc

        score = calculate_gameweek_score(
            fpl_gameweek=fpl_gameweek,
            rules=rules,
        )

        prepared_results.append(
            (
                league_member_id,
                fpl_gameweek,
                score,
            )
        )

    synced_at = datetime.now(timezone.utc)

    response_results: list[GameweekSyncMemberResponse] = []

    async with db.begin():
        for (
            league_member_id,
            fpl_gameweek,
            score,
        ) in prepared_results:
            result = await db.scalar(
                select(GameweekResult).where(
                    GameweekResult.league_id == league_id,
                    GameweekResult.league_member_id == league_member_id,
                    GameweekResult.gameweek == gameweek,
                )
            )

            if result is None:
                result = GameweekResult(
                    league_id=league_id,
                    league_member_id=(league_member_id),
                    gameweek=gameweek,
                    status=result_status,
                    gross_points=(score.gross_points),
                    transfer_deduction=(score.transfer_deduction),
                    net_points=(score.net_points),
                    scoreboard_points=(score.scoreboard_points),
                    transfers_made=(score.transfers_made),
                    points_on_bench=(score.points_on_bench),
                    chip_used=(score.chip_used.value if score.chip_used else None),
                    chip_allowed=(score.chip_allowed),
                    eligible=score.eligible,
                    ineligibility_reason=(score.ineligibility_reason),
                    synced_at=synced_at,
                )

                db.add(result)

                await db.flush()

            else:
                result.status = result_status
                result.gross_points = score.gross_points
                result.transfer_deduction = score.transfer_deduction
                result.net_points = score.net_points
                result.scoreboard_points = score.scoreboard_points
                result.transfers_made = score.transfers_made
                result.points_on_bench = score.points_on_bench
                result.chip_used = score.chip_used.value if score.chip_used else None
                result.chip_allowed = score.chip_allowed
                result.eligible = score.eligible
                result.ineligibility_reason = score.ineligibility_reason
                result.synced_at = synced_at

                await db.flush()

            await db.execute(
                delete(GameweekPick).where(GameweekPick.gameweek_result_id == result.id)
            )

            picks = [
                GameweekPick(
                    gameweek_result_id=result.id,
                    element_id=pick.element_id,
                    player_name=pick.player_name,
                    team_id=pick.team_id,
                    team_name=pick.team_name,
                    team_short_name=(pick.team_short_name),
                    player_position=(pick.player_position.value),
                    squad_position=(pick.squad_position),
                    is_starter=(pick.is_starter),
                    gameweek_points=(pick.gameweek_points),
                    points_contribution=(pick.points_contribution),
                    multiplier=pick.multiplier,
                    is_captain=(pick.is_captain),
                    is_vice_captain=(pick.is_vice_captain),
                )
                for pick in fpl_gameweek.picks
            ]

            db.add_all(picks)

            response_results.append(
                GameweekSyncMemberResponse(
                    league_member_id=(league_member_id),
                    entry_id=score.entry_id,
                    scoreboard_points=(score.scoreboard_points),
                    chip_used=(score.chip_used),
                    eligible=(score.eligible),
                    ineligibility_reason=(score.ineligibility_reason),
                )
            )

    if result_status == GameweekResultStatus.FINAL:
        async with db.begin():
            await _create_gameweek_winner_notifications(
                db=db,
                league_id=league_id,
                league_slug=league_slug,
                gameweek=gameweek,
            )

    await invalidate_gameweek_cache(
        slug=league_slug,
        gameweek=gameweek,
        member_ids=[
            result.league_member_id
            for result in response_results
        ],
    )

    return LeagueGameweekSyncResponse(
        league_slug=league_slug,
        gameweek=gameweek,
        status=result_status,
        synced_members=len(response_results),
        results=response_results,
    )


def _get_ineligibility_label(
    result: GameweekResult,
) -> str | None:
    if result.ineligibility_reason is None:
        return None

    if result.ineligibility_reason == GameweekIneligibilityReason.PROHIBITED_CHIP:
        chip_label = CHIP_LABELS.get(
            result.chip_used or "",
            result.chip_used or "Unknown chip",
        )

        return f"Prohibited chip: {chip_label}"

    return result.ineligibility_reason.value


def _ranking_key(
    result: GameweekResult,
) -> tuple[int, int, int]:
    used_chip = 1 if result.chip_used is not None else 0

    return (
        -result.scoreboard_points,
        used_chip,
        result.transfer_deduction,
    )


def _tie_key(
    result: GameweekResult,
) -> tuple[int, bool, int]:
    return (
        result.scoreboard_points,
        result.chip_used is not None,
        result.transfer_deduction,
    )


def _rank_results(
    rows: list[tuple[GameweekResult, int]],
) -> list[GameweekStandingResponse]:
    eligible_rows = [row for row in rows if row[0].eligible]

    ineligible_rows = [row for row in rows if not row[0].eligible]

    eligible_rows.sort(
        key=lambda row: (
            *_ranking_key(row[0]),
            row[1],
        )
    )

    # Ineligible users are always below
    # competitive standings.
    ineligible_rows.sort(
        key=lambda row: (
            -row[0].scoreboard_points,
            row[0].transfer_deduction,
            row[1],
        )
    )

    standings: list[GameweekStandingResponse] = []

    previous_tie_key = None
    current_rank = 0

    for index, (
        result,
        fpl_entry_id,
    ) in enumerate(
        eligible_rows,
        start=1,
    ):
        tie_key = _tie_key(result)

        if tie_key != previous_tie_key:
            current_rank = index

        standings.append(
            GameweekStandingResponse(
                rank=current_rank,
                league_member_id=(result.league_member_id),
                fpl_entry_id=fpl_entry_id,
                gross_points=(result.gross_points),
                transfer_deduction=(result.transfer_deduction),
                net_points=(result.net_points),
                scoreboard_points=(result.scoreboard_points),
                transfers_made=(result.transfers_made),
                points_on_bench=(result.points_on_bench),
                chip_used=result.chip_used,
                chip_allowed=(result.chip_allowed),
                eligible=True,
                ineligibility_reason=None,
                ineligibility_label=None,
            )
        )

        previous_tie_key = tie_key

    for (
        result,
        fpl_entry_id,
    ) in ineligible_rows:
        standings.append(
            GameweekStandingResponse(
                rank=None,
                league_member_id=(result.league_member_id),
                fpl_entry_id=fpl_entry_id,
                gross_points=(result.gross_points),
                transfer_deduction=(result.transfer_deduction),
                net_points=(result.net_points),
                scoreboard_points=(result.scoreboard_points),
                transfers_made=(result.transfers_made),
                points_on_bench=(result.points_on_bench),
                chip_used=result.chip_used,
                chip_allowed=(result.chip_allowed),
                eligible=False,
                ineligibility_reason=(result.ineligibility_reason),
                ineligibility_label=(_get_ineligibility_label(result)),
            )
        )

    return standings


async def _create_gameweek_winner_notifications(
    db: AsyncSession,
    *,
    league_id: int,
    league_slug: str,
    gameweek: int,
) -> None:
    rows = await _get_gameweek_result_rows(
        db=db,
        league_id=league_id,
        gameweek=gameweek,
    )

    if not rows:
        return

    standings = _rank_results(rows)
    winners = [
        standing
        for standing in standings
        if standing.eligible and standing.rank == 1
    ]

    if not winners:
        return

    winner_member_ids = [
        winner.league_member_id for winner in winners
    ]

    winner_result = await db.execute(
        select(
            LeagueMember.id,
            LeagueMember.fpl_entry_id,
            FPLAccount.team_name,
        )
        .outerjoin(
            FPLAccount,
            FPLAccount.user_id == LeagueMember.user_id,
        )
        .where(LeagueMember.id.in_(winner_member_ids))
    )

    winner_names = {
        member_id: team_name or f"Entry {fpl_entry_id}"
        for member_id, fpl_entry_id, team_name in winner_result.all()
    }
    winning_score = winners[0].scoreboard_points
    names = [
        winner_names.get(
            winner.league_member_id,
            f"Entry {winner.fpl_entry_id}",
        )
        for winner in winners
    ]

    if len(names) == 1:
        body = (
            f"{names[0]} won Gameweek {gameweek} "
            f"with {winning_score} points."
        )
    elif len(names) == 2:
        body = (
            f"{names[0]} and {names[1]} tied for "
            f"Gameweek {gameweek} with {winning_score} points."
        )
    else:
        body = (
            f"{', '.join(names[:-1])}, and {names[-1]} tied "
            f"for Gameweek {gameweek} with {winning_score} points."
        )

    recipients_result = await db.execute(
        select(LeagueMember.user_id).where(
            LeagueMember.league_id == league_id,
            LeagueMember.status == LeagueMemberStatus.APPROVED,
            LeagueMember.user_id.is_not(None),
        )
    )

    recipient_user_ids = recipients_result.scalars().all()

    for user_id in recipient_user_ids:
        await notify_gameweek_winner(
            db=db,
            user_id=user_id,
            league_id=league_id,
            league_slug=league_slug,
            gameweek=gameweek,
            body=body,
        )


async def _get_gameweek_result_rows(
    db: AsyncSession,
    league_id: int,
    gameweek: int,
) -> list[tuple[GameweekResult, int]]:
    result = await db.execute(
        select(
            GameweekResult,
            LeagueMember.fpl_entry_id,
        )
        .join(
            LeagueMember,
            LeagueMember.id == GameweekResult.league_member_id,
        )
        .where(
            GameweekResult.league_id == league_id,
            GameweekResult.gameweek == gameweek,
        )
    )

    return [
        (
            row[0],
            row[1],
        )
        for row in result.all()
    ]


async def _validate_gameweek_started_for_missing_result(
    gameweek: int,
) -> None:
    bootstrap = await get_cached_bootstrap_static()

    if bootstrap is None:
        bootstrap = await get_bootstrap_static()

    event = _get_gameweek_event(
        bootstrap=bootstrap,
        gameweek=gameweek,
    )
    validate_gameweek_started(event)


async def get_league_gameweek(
    db: AsyncSession,
    slug: str,
    gameweek: int,
    *,
    user_id: int,
) -> LeagueGameweekResponse:
    league = await db.scalar(
        select(League).where(
            League.slug == slug,
        )
    )

    if league is None:
        raise GameweekLeagueNotFoundError

    await require_approved_league_member(
        db=db,
        league_id=league.id,
        user_id=user_id,
    )

    rules = await db.scalar(
        select(LeagueRules).where(
            LeagueRules.league_id == league.id,
        )
    )

    if rules is None:
        raise GameweekLeagueRulesNotFoundError

    if gameweek < rules.start_gameweek:
        raise GameweekBeforeLeagueStartError

    cache_key = standings_cache_key(
        slug,
        gameweek,
    )

    cached = await get_cached_model(
        cache_key,
        LeagueGameweekResponse,
    )

    if cached is not None:
        return cached

    rows = await _get_gameweek_result_rows(
        db=db,
        league_id=league.id,
        gameweek=gameweek,
    )

    if not rows:
        await _validate_gameweek_started_for_missing_result(gameweek)
        raise GameweekResultsNotFoundError

    standings = _rank_results(rows)

    result_status = (
        GameweekResultStatus.LIVE
        if any(result.status == GameweekResultStatus.LIVE for result, _ in rows)
        else GameweekResultStatus.FINAL
    )

    response = LeagueGameweekResponse(
        league_slug=league.slug,
        gameweek=gameweek,
        status=result_status,
        standings=standings,
    )

    await set_cached_model(
        key=cache_key,
        value=response,
        ttl=gameweek_response_ttl(
            result_status,
        ),
    )

    return response


async def get_member_gameweek(
    db: AsyncSession,
    slug: str,
    gameweek: int,
    member_id: int,
    *,
    user_id: int,
) -> MemberGameweekResponse:
    league = await db.scalar(
        select(League).where(
            League.slug == slug,
        )
    )

    if league is None:
        raise GameweekLeagueNotFoundError

    await require_approved_league_member(
        db=db,
        league_id=league.id,
        user_id=user_id,
    )

    rules = await db.scalar(
        select(LeagueRules).where(
            LeagueRules.league_id == league.id,
        )
    )

    if rules is None:
        raise GameweekLeagueRulesNotFoundError

    if gameweek < rules.start_gameweek:
        raise GameweekBeforeLeagueStartError

    cache_key = member_gameweek_cache_key(
        slug,
        gameweek,
        member_id,
    )

    cached = await get_cached_model(
        cache_key,
        MemberGameweekResponse,
    )

    if cached is not None:
        return cached

    rows = await _get_gameweek_result_rows(
        db=db,
        league_id=league.id,
        gameweek=gameweek,
    )

    if not rows:
        await _validate_gameweek_started_for_missing_result(gameweek)
        raise GameweekResultsNotFoundError

    standings = _rank_results(rows)

    standing = next(
        (item for item in standings if item.league_member_id == member_id),
        None,
    )

    if standing is None:
        raise GameweekMemberResultNotFoundError

    result = await db.scalar(
        select(GameweekResult).where(
            GameweekResult.league_id == league.id,
            GameweekResult.league_member_id == member_id,
            GameweekResult.gameweek == gameweek,
        )
    )

    if result is None:
        raise GameweekMemberResultNotFoundError

    picks_result = await db.execute(
        select(GameweekPick)
        .where(
            GameweekPick.gameweek_result_id == result.id,
        )
        .order_by(
            GameweekPick.squad_position.asc(),
        )
    )

    picks = picks_result.scalars().all()

    response = MemberGameweekResponse(
        league_member_id=member_id,
        fpl_entry_id=standing.fpl_entry_id,
        gameweek=gameweek,
        status=result.status,
        rank=standing.rank,
        gross_points=result.gross_points,
        transfer_deduction=(result.transfer_deduction),
        net_points=result.net_points,
        scoreboard_points=(result.scoreboard_points),
        transfers_made=(result.transfers_made),
        points_on_bench=(result.points_on_bench),
        chip_used=result.chip_used,
        chip_allowed=result.chip_allowed,
        eligible=result.eligible,
        ineligibility_reason=(result.ineligibility_reason),
        ineligibility_label=(_get_ineligibility_label(result)),
        picks=[
            GameweekPickResponse(
                element_id=pick.element_id,
                player_name=pick.player_name,
                team_id=pick.team_id,
                team_name=pick.team_name,
                team_short_name=(pick.team_short_name),
                player_position=(FPLPlayerPosition(pick.player_position)),
                squad_position=(pick.squad_position),
                is_starter=pick.is_starter,
                gameweek_points=(pick.gameweek_points),
                points_contribution=(pick.points_contribution),
                multiplier=pick.multiplier,
                is_captain=pick.is_captain,
                is_vice_captain=(pick.is_vice_captain),
            )
            for pick in picks
        ],
    )

    await set_cached_model(
        key=cache_key,
        value=response,
        ttl=gameweek_response_ttl(result.status),
    )

    return response


async def sync_league_gameweek_as_owner(
    db: AsyncSession,
    slug: str,
    gameweek: int,
    owner_user_id: int,
) -> LeagueGameweekSyncResponse:
    async with db.begin():
        league = await db.scalar(
            select(League).where(
                League.slug == slug,
            )
        )

        if league is None:
            raise GameweekLeagueNotFoundError

        try:
            await _require_owner(
                db=db,
                league_id=league.id,
                user_id=owner_user_id,
            )
        except LeagueOwnerRequiredError as exc:
            raise GameweekSyncOwnerRequiredError from exc

    return await sync_league_gameweek(
        db=db,
        slug=slug,
        gameweek=gameweek,
    )
