from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from app.models.gameweek_result import GameweekResultStatus
from app.schemas.gameweek import (
    GameweekStandingResponse,
    LeagueGameweekResponse,
)
from app.services import gameweek


def _standing(
    *,
    entry_id: int,
    rank: int | None,
    score: int,
    eligible: bool,
) -> GameweekStandingResponse:
    return GameweekStandingResponse(
        rank=rank,
        league_member_id=entry_id,
        fpl_entry_id=entry_id,
        gross_points=score,
        transfer_deduction=0,
        net_points=score,
        scoreboard_points=score,
        transfers_made=0,
        points_on_bench=0,
        chip_used=None,
        chip_allowed=True,
        eligible=eligible,
        ineligibility_reason=None,
        ineligibility_label=None,
    )


class LeagueGameweekSummaryTests(IsolatedAsyncioTestCase):
    async def test_summary_uses_ranked_leader_and_current_user_score(self):
        response = LeagueGameweekResponse(
            league_slug="private-league",
            gameweek=5,
            status=GameweekResultStatus.LIVE,
            standings=[
                _standing(entry_id=10, rank=1, score=80, eligible=True),
                _standing(entry_id=20, rank=None, score=90, eligible=False),
            ],
        )
        db = SimpleNamespace(scalar=AsyncMock(return_value=20))

        with patch.object(
            gameweek,
            "get_league_gameweek",
            new_callable=AsyncMock,
            return_value=response,
        ):
            summary = await gameweek.get_league_gameweek_summary(
                db=db,
                slug="private-league",
                gameweek=5,
                user_id=2,
            )

        self.assertIsNone(summary.current_user_rank)
        self.assertEqual(summary.current_user_score, 90)
        self.assertEqual(summary.winner_score, 80)

    async def test_summary_has_no_winner_when_all_members_are_ineligible(self):
        response = LeagueGameweekResponse(
            league_slug="private-league",
            gameweek=5,
            status=GameweekResultStatus.FINAL,
            standings=[
                _standing(entry_id=20, rank=None, score=90, eligible=False),
            ],
        )
        db = SimpleNamespace(scalar=AsyncMock(return_value=20))

        with patch.object(
            gameweek,
            "get_league_gameweek",
            new_callable=AsyncMock,
            return_value=response,
        ):
            summary = await gameweek.get_league_gameweek_summary(
                db=db,
                slug="private-league",
                gameweek=5,
                user_id=2,
            )

        self.assertIsNone(summary.current_user_rank)
        self.assertEqual(summary.current_user_score, 90)
        self.assertIsNone(summary.winner_score)
