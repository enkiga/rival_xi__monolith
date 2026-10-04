from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx

from app.api.dependencies.auth import get_current_auth
from app.api.v1.fpl import router as fpl_router
from app.api.v1.onboarding import router as onboarding_router
from app.integrations.fpl_rivals import client as fpl_rivals_client
from app.integrations.fpl_rivals.client import (
    FPLManagerSearchUpstreamError,
    search_fpl_managers,
)
from app.schemas.onboarding import (
    FPLManagerSearchResponse,
    FPLManagerSearchResult,
)
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
            "/api/v1/leagues/{slug}/invitation-link",
            paths,
        )
        self.assertIn(
            "/api/v1/leagues/{slug}/invitation-link/regenerate",
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


class ManagerSearchClientTests(IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await fpl_rivals_client.close_fpl_rivals_client()

    async def test_provider_results_are_normalized(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params["q"], "Kevin Garoli")
            self.assertEqual(request.url.params["type"], "manager")
            self.assertEqual(request.url.params["limit"], "7")

            return httpx.Response(
                200,
                json={
                    "data": {
                        "managers": [
                            {
                                "id": 4250337,
                                "player_name": "Kevin Garoli",
                                "entry_name": "Rival XI",
                            }
                        ]
                    }
                },
            )

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        self.assertEqual(
            await search_fpl_managers("Kevin Garoli"),
            [
                FPLManagerSearchResult(
                    entry_id=4250337,
                    manager_name="Kevin Garoli",
                    team_name="Rival XI",
                )
            ],
        )

    async def test_malformed_provider_result_is_unavailable(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"data": {"managers": [{"id": "invalid"}]}},
            )

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        with self.assertRaises(FPLManagerSearchUpstreamError):
            await search_fpl_managers("Kevin Garoli")

    async def test_no_provider_results_returns_empty_list(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"managers": []}})

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        self.assertEqual(await search_fpl_managers("Unknown"), [])

    async def test_provider_results_are_capped_at_seven(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "managers": [
                            {
                                "id": entry_id,
                                "player_name": f"Manager {entry_id}",
                                "entry_name": f"Team {entry_id}",
                            }
                            for entry_id in range(1, 9)
                        ]
                    }
                },
            )

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        results = await search_fpl_managers("Manager")

        self.assertEqual(len(results), 7)

    async def test_provider_timeout_is_unavailable(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("Timed out", request=request)

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        with self.assertRaises(FPLManagerSearchUpstreamError):
            await search_fpl_managers("Kevin Garoli")

    async def test_provider_http_failure_is_unavailable(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429)

        fpl_rivals_client._http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler),
            base_url="https://example.test",
        )

        with self.assertRaises(FPLManagerSearchUpstreamError):
            await search_fpl_managers("Kevin Garoli")


class ManagerSearchRouteTests(TestCase):
    def setUp(self):
        self.api = FastAPI()
        self.api.include_router(onboarding_router, prefix="/onboarding")
        self.client = TestClient(self.api)

    def test_search_requires_authentication(self):
        response = self.client.get("/onboarding/fpl/search?q=Kevin")

        self.assertEqual(response.status_code, 401)

    def test_short_query_is_rejected(self):
        self.api.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(
            user_id=1
        )

        response = self.client.get("/onboarding/fpl/search?q=Ke")

        self.assertEqual(response.status_code, 422)

    def test_authenticated_search_succeeds(self):
        self.api.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(
            user_id=1
        )

        result = FPLManagerSearchResponse(
            results=[
                FPLManagerSearchResult(
                    entry_id=4250337,
                    manager_name="Kevin Garoli",
                    team_name="Rival XI",
                )
            ]
        )

        with patch(
            "app.api.v1.onboarding.search_fpl_manager_candidates",
            new=AsyncMock(return_value=result),
        ):
            response = self.client.get(
                "/onboarding/fpl/search?q=Kevin%20Garoli"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), result.model_dump())

    def test_provider_failure_degrades_to_manual_fallback(self):
        self.api.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(
            user_id=1
        )

        with patch(
            "app.api.v1.onboarding.search_fpl_manager_candidates",
            new=AsyncMock(side_effect=FPLManagerSearchUpstreamError),
        ):
            response = self.client.get("/onboarding/fpl/search?q=Kevin")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"results": [], "search_available": False},
        )
