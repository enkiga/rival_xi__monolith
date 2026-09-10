from app.integrations.fpl.client import (
    get_bootstrap_static,
    get_entry_gameweek_picks,
    get_event_live,
    get_fpl_entry,
)
from app.models.league_rules import FPLChip
from app.schemas.fpl import (
    FPLGameweekPickResponse,
    FPLGameweekResponse,
    FPLManagerResponse,
    FPLPlayerPosition,
)


class CurrentGameweekNotFoundError(Exception):
    pass


class FPLGameweekNotFoundError(Exception):
    pass


class UnsupportedFPLChipError(Exception):
    pass


class FPLPlayerNotFoundError(Exception):
    pass


class UnsupportedFPLPositionError(Exception):
    pass


FPL_CHIP_MAP: dict[str, FPLChip] = {
    "wildcard": FPLChip.WILDCARD,
    "freehit": FPLChip.FREE_HIT,
    "bboost": FPLChip.BENCH_BOOST,
    "3xc": FPLChip.TRIPLE_CAPTAIN,
}


POSITION_MAP: dict[str, FPLPlayerPosition] = {
    "GKP": FPLPlayerPosition.GOALKEEPER,
    "DEF": FPLPlayerPosition.DEFENDER,
    "MID": FPLPlayerPosition.MIDFIELDER,
    "FWD": FPLPlayerPosition.FORWARD,
}


async def find_fpl_manager(
    entry_id: int,
) -> FPLManagerResponse | None:
    entry = await get_fpl_entry(entry_id)

    if entry is None:
        return None

    first_name = entry.get(
        "player_first_name",
        "",
    )
    last_name = entry.get(
        "player_last_name",
        "",
    )

    manager_name = f"{first_name} {last_name}".strip()

    return FPLManagerResponse(
        entry_id=entry["id"],
        team_name=entry["name"],
        manager_name=manager_name,
        overall_points=entry.get("summary_overall_points"),
        overall_rank=entry.get("summary_overall_rank"),
    )


async def get_current_gameweek() -> int:
    bootstrap = await get_bootstrap_static()

    events = bootstrap.get(
        "events",
        [],
    )

    for event in events:
        if event.get("is_current"):
            return event["id"]

    for event in events:
        if event.get("is_next"):
            return event["id"]

    raise CurrentGameweekNotFoundError


async def get_fpl_gameweek(
    entry_id: int,
    gameweek: int,
    *,
    bootstrap: dict | None = None,
    live_data: dict | None = None,
) -> FPLGameweekResponse:
    data = await get_entry_gameweek_picks(
        entry_id=entry_id,
        gameweek=gameweek,
    )

    if data is None:
        raise FPLGameweekNotFoundError

    entry_history = data.get("entry_history")

    if entry_history is None:
        raise FPLGameweekNotFoundError

    if bootstrap is None:
        bootstrap = await get_bootstrap_static()

    if live_data is None:
        live_data = await get_event_live(
            gameweek=gameweek,
        )

    players_by_id = {
        player["id"]: player
        for player in bootstrap.get(
            "elements",
            [],
        )
    }

    element_types_by_id = {
        element_type["id"]: element_type
        for element_type in bootstrap.get(
            "element_types",
            [],
        )
    }

    teams_by_id = {
        team["id"]: team
        for team in bootstrap.get(
            "teams",
            [],
        )
    }

    player_points_by_id = {
        element["id"]: element.get(
            "stats",
            {},
        ).get(
            "total_points",
            0,
        )
        for element in live_data.get(
            "elements",
            [],
        )
    }

    gross_points = entry_history.get(
        "points",
        0,
    )

    transfer_deduction = entry_history.get(
        "event_transfers_cost",
        0,
    )

    net_points = gross_points - transfer_deduction

    active_chip = data.get("active_chip")

    chip_used: FPLChip | None = None

    if active_chip:
        chip_used = FPL_CHIP_MAP.get(active_chip)

        if chip_used is None:
            raise UnsupportedFPLChipError(active_chip)

    picks: list[FPLGameweekPickResponse] = []

    for pick in data.get(
        "picks",
        [],
    ):
        element_id = pick["element"]

        player = players_by_id.get(element_id)

        if player is None:
            raise FPLPlayerNotFoundError(element_id)

        element_type = element_types_by_id.get(player["element_type"])

        if element_type is None:
            raise UnsupportedFPLPositionError(player["element_type"])

        position_code = element_type.get("singular_name_short")

        player_position = POSITION_MAP.get(position_code)

        if player_position is None:
            raise UnsupportedFPLPositionError(position_code)

        team = teams_by_id.get(player["team"])

        if team is None:
            raise FPLPlayerNotFoundError(element_id)

        squad_position = pick["position"]

        multiplier = pick["multiplier"]

        gameweek_points = player_points_by_id.get(
            element_id,
            0,
        )

        points_contribution = gameweek_points * multiplier

        picks.append(
            FPLGameweekPickResponse(
                element_id=element_id,
                player_name=player["web_name"],
                team_id=team["id"],
                team_name=team["name"],
                team_short_name=team["short_name"],
                player_position=(player_position),
                squad_position=(squad_position),
                is_starter=(squad_position <= 11),
                gameweek_points=(gameweek_points),
                points_contribution=(points_contribution),
                multiplier=multiplier,
                is_captain=pick["is_captain"],
                is_vice_captain=pick["is_vice_captain"],
            )
        )

    return FPLGameweekResponse(
        entry_id=entry_id,
        gameweek=gameweek,
        gross_points=gross_points,
        transfer_deduction=(transfer_deduction),
        net_points=net_points,
        transfers_made=entry_history.get(
            "event_transfers",
            0,
        ),
        points_on_bench=entry_history.get(
            "points_on_bench",
            0,
        ),
        chip_used=chip_used,
        picks=picks,
    )
