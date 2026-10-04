from app.schemas.fpl import FPLPlayerPosition


FPL_KIT_ASSET_BASE_URL = (
    "https://fantasy.premierleague.com/dist/img/shirts/standard"
)


def get_fpl_kit_url(
    *,
    team_code: int,
    player_position: FPLPlayerPosition,
) -> str:
    goalkeeper_suffix = (
        "_1" if player_position == FPLPlayerPosition.GOALKEEPER else ""
    )

    return (
        f"{FPL_KIT_ASSET_BASE_URL}/"
        f"shirt_{team_code}{goalkeeper_suffix}-110.webp"
    )


def get_fpl_kit_url_from_bootstrap(
    *,
    bootstrap: dict,
    team_id: int,
    player_position: FPLPlayerPosition,
) -> str | None:
    team = next(
        (
            team
            for team in bootstrap.get("teams", [])
            if team.get("id") == team_id
        ),
        None,
    )

    if team is None or team.get("code") is None:
        return None

    return get_fpl_kit_url(
        team_code=team["code"],
        player_position=player_position,
    )
