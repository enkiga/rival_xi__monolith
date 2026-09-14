from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_auth
from app.api.v1.fpl import router as fpl_router
from app.integrations.fpl.client import FPLUpstreamError
from app.main import app
from app.services import gameweek
from app.services.gameweek import (
    FutureGameweekError,
    GameweekBeforeLeagueStartError,
)
from app.services.onboarding import (
    InvalidFPLReferenceError,
    extract_fpl_entry_id,
)


class CompletionRouteTests(TestCase):
    def test_final_invitation_paths_and_direct_join_removal(self):
        paths = app.openapi()["paths"]

        self.assertIn(
            "/api/v1/leagues/{slug}/invitations",
            paths,
        )
        self.assertIn(
            "/api/v1/invitations/{token}",
            paths,
        )
        self.assertNotIn(
            "/api/v1/invitations/invitations/{token}",
            paths,
        )
        self.assertNotIn(
            "post",
            paths.get(
                "/api/v1/leagues/{slug}/members",
                {},
            ),
        )

    def test_fpl_utilities_require_authentication(self):
        api = FastAPI()
        api.include_router(fpl_router, prefix="/fpl")
        client = TestClient(api)

        self.assertEqual(client.get("/fpl/teams/1").status_code, 401)
        self.assertEqual(
            client.get("/fpl/teams/1/gameweeks/1").status_code,
            401,
        )

    def test_fpl_upstream_failure_is_bad_gateway(self):
        api = FastAPI()
        api.include_router(fpl_router, prefix="/fpl")
        api.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(
            user_id=1
        )
        client = TestClient(api)

        with patch(
            "app.api.v1.fpl.find_fpl_manager",
            new_callable=AsyncMock,
            side_effect=FPLUpstreamError,
        ):
            self.assertEqual(client.get("/fpl/teams/1").status_code, 502)


class GameweekReadConsistencyTests(IsolatedAsyncioTestCase):
    async def test_missing_bootstrap_falls_back_to_fpl_for_future_check(self):
        future_deadline = datetime.now(timezone.utc) + timedelta(days=1)

        with (
            patch.object(
                gameweek,
                "get_cached_bootstrap_static",
                new=AsyncMock(return_value=None),
            ),
            patch.object(
                gameweek,
                "get_bootstrap_static",
                new=AsyncMock(
                    return_value={
                        "events": [
                            {
                                "id": 4,
                                "deadline_time": future_deadline.isoformat(),
                            }
                        ]
                    }
                ),
            ) as get_bootstrap,
        ):
            with self.assertRaises(FutureGameweekError):
                await gameweek._validate_gameweek_started_for_missing_result(4)

            get_bootstrap.assert_awaited_once()

    async def test_squad_read_checks_league_start_before_cache(self):
        db = SimpleNamespace(
            scalar=AsyncMock(
                side_effect=[
                    SimpleNamespace(id=1),
                    SimpleNamespace(start_gameweek=5),
                ]
            )
        )

        with (
            patch.object(
                gameweek,
                "require_approved_league_member",
                new_callable=AsyncMock,
            ),
            patch.object(
                gameweek,
                "get_cached_model",
                new_callable=AsyncMock,
            ) as get_cached,
        ):
            with self.assertRaises(GameweekBeforeLeagueStartError):
                await gameweek.get_member_gameweek(
                    db=db,
                    slug="private",
                    gameweek=4,
                    member_id=3,
                    user_id=2,
                )

            get_cached.assert_not_awaited()


class OnboardingReferenceTests(TestCase):
    def test_numeric_and_url_entry_references(self):
        self.assertEqual(extract_fpl_entry_id("12345"), 12345)
        self.assertEqual(
            extract_fpl_entry_id(
                "https://fantasy.premierleague.com/entry/12345/event/4"
            ),
            12345,
        )

    def test_invalid_reference_is_rejected(self):
        with self.assertRaises(InvalidFPLReferenceError):
            extract_fpl_entry_id("not-an-entry")
