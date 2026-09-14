"""Regression checks for session-based league authorization.

Run from backend with: python -m unittest discover -s tests
"""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies.auth import get_current_auth
from app.api.v1.league import router
from app.db.session import get_db
from app.schemas.league import LeagueCreate, LeagueUpdate
from app.services.gameweek import GameweekSyncOwnerRequiredError
from app.services.league import FPLAccountRequiredError, LeagueOwnerRequiredError
from app.services.league_access import (
    LeagueMembershipPendingError,
    LeagueMembershipRequiredError,
)


class LeagueAuthorizationTests(TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix="/leagues")
        self.db = object()
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(self.app)

    def authenticate(self):
        self.app.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(user_id=42)

    def test_protected_league_endpoints_require_authentication(self):
        for method, path, body in (
            ("post", "/leagues", {"name": "Test league", "rules": {
                "start_gameweek": 1, "include_transfer_deductions": True,
                "allowed_chips": [],
            }}),
            ("patch", "/leagues/test/members/7/approve", None),
            ("patch", "/leagues/test/members/7/reject", None),
            ("patch", "/leagues/test/activate", None),
            ("patch", "/leagues/test", {"name": "Changed league"}),
            ("post", "/leagues/test/gameweeks/1/sync", None),
            ("get", "/leagues/test", None),
            ("get", "/leagues/test/gameweeks/1", None),
            ("get", "/leagues/test/gameweeks/1/members/7", None),
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.request(method, path, json=body).status_code, 401)

    def test_league_reads_use_session_and_map_membership_errors(self):
        self.authenticate()
        for path, service, error, detail in (
            (
                "/leagues/test",
                "get_league",
                LeagueMembershipPendingError,
                "Your league membership is awaiting approval",
            ),
            (
                "/leagues/test/gameweeks/1",
                "get_league_gameweek",
                LeagueMembershipRequiredError,
                "Approved league membership is required",
            ),
            (
                "/leagues/test/gameweeks/1/members/7",
                "get_member_gameweek",
                LeagueMembershipRequiredError,
                "Approved league membership is required",
            ),
        ):
            with self.subTest(service=service), patch(
                f"app.api.v1.league.{service}",
                new_callable=AsyncMock,
                side_effect=error,
            ) as mocked:
                response = self.client.get(path)

                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["detail"], detail)
                self.assertEqual(mocked.await_args.kwargs["user_id"], 42)

    def test_owner_actions_use_session_even_with_forged_identity(self):
        self.authenticate()
        for method, path, service, error in (
            ("patch", "/leagues/test/members/7/approve", "approve_league_member", LeagueOwnerRequiredError),
            ("patch", "/leagues/test/members/7/reject", "reject_league_member", LeagueOwnerRequiredError),
            ("patch", "/leagues/test/activate", "activate_league", LeagueOwnerRequiredError),
            ("patch", "/leagues/test", "update_league", LeagueOwnerRequiredError),
            ("post", "/leagues/test/gameweeks/1/sync", "sync_league_gameweek_as_owner", GameweekSyncOwnerRequiredError),
        ):
            with self.subTest(service=service), patch(
                f"app.api.v1.league.{service}", new_callable=AsyncMock,
                side_effect=error,
            ) as mocked:
                response = self.client.request(method, path, json={
                    "name": "Changed league", "owner_fpl_entry_id": 999,
                    "owner_user_id": 999,
                })
                self.assertEqual(response.status_code, 403)
                self.assertEqual(mocked.await_args.kwargs["owner_user_id"], 42)
                self.assertNotIn("owner_fpl_entry_id", mocked.await_args.kwargs)

    def test_direct_join_route_is_not_exposed(self):
        schema = self.app.openapi()

        self.assertNotIn(
            "post",
            schema["paths"].get(
                "/leagues/{slug}/members",
                {},
            ),
        )

    def test_create_needs_no_fpl_id_and_missing_account_is_conflict(self):
        self.authenticate()
        with patch("app.api.v1.league.create_league", new_callable=AsyncMock,
                   side_effect=FPLAccountRequiredError) as mocked:
            response = self.client.post("/leagues", json={
                "name": "Test league", "rules": {"start_gameweek": 1,
                "include_transfer_deductions": True, "allowed_chips": []},
            })
            self.assertEqual(response.status_code, 409)
            self.assertEqual(mocked.await_args.kwargs["user_id"], 42)

    def test_schema_excludes_identity_and_preserves_update_validation(self):
        self.assertNotIn("fpl_entry_id", LeagueCreate.model_fields)
        self.assertNotIn("owner_fpl_entry_id", LeagueUpdate.model_fields)
        with self.assertRaises(ValidationError):
            LeagueUpdate()
        self.assertEqual(LeagueUpdate(name=" New name ").name, "New name")
        schema = self.app.openapi()
        for path, method in (
            ("/leagues/{slug}/members/{member_id}/approve", "patch"),
            ("/leagues/{slug}/members/{member_id}/reject", "patch"),
            ("/leagues/{slug}/activate", "patch"),
            ("/leagues/{slug}/gameweeks/{gameweek}/sync", "post"),
        ):
            self.assertNotIn("requestBody", schema["paths"][path][method])
