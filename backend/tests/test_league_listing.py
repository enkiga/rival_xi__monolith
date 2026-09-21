from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_auth
from app.api.v1.league import router
from app.db.session import get_db
from app.models.league import LeagueStatus
from app.models.league_member import LeagueMemberRole, LeagueMemberStatus
from app.schemas.league import LeagueListResponse
from app.services.league import get_user_leagues


class LeagueListingRouteTests(TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix="/leagues")
        self.db = object()
        self.app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(self.app)

    def test_listing_requires_authentication(self):
        response = self.client.get("/leagues")

        self.assertEqual(response.status_code, 401)

    def test_listing_passes_filters_and_pagination(self):
        self.app.dependency_overrides[get_current_auth] = lambda: SimpleNamespace(
            user_id=42
        )
        empty_page = LeagueListResponse(
            items=[],
            total=0,
            page=2,
            page_size=10,
            pages=0,
        )

        with patch(
            "app.api.v1.league.get_user_leagues",
            new_callable=AsyncMock,
            return_value=empty_page,
        ) as get_leagues:
            response = self.client.get(
                "/leagues",
                params={
                    "page": 2,
                    "page_size": 10,
                    "search": "friends",
                    "sort_by": "name",
                    "sort_order": "asc",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"], [])
        get_leagues.assert_awaited_once_with(
            db=self.db,
            user_id=42,
            page=2,
            page_size=10,
            search="friends",
            sort_by="name",
            sort_order="asc",
        )


class LeagueListingServiceTests(IsolatedAsyncioTestCase):
    async def test_empty_listing_returns_pagination_metadata(self):
        rows = Mock()
        rows.all.return_value = []
        db = SimpleNamespace(
            scalar=AsyncMock(return_value=0),
            execute=AsyncMock(return_value=rows),
        )

        response = await get_user_leagues(
            db=db,
            user_id=42,
            page=3,
            page_size=20,
            search=None,
            sort_by="created_at",
            sort_order="desc",
        )

        self.assertEqual(response.items, [])
        self.assertEqual(response.total, 0)
        self.assertEqual(response.page, 3)
        self.assertEqual(response.page_size, 20)
        self.assertEqual(response.pages, 0)

        list_query = db.execute.await_args.args[0]
        parameters = list_query.compile().params.values()
        self.assertIn(20, parameters)
        self.assertIn(40, parameters)

    async def test_listing_searches_by_name(self):
        rows = Mock()
        rows.all.return_value = []
        db = SimpleNamespace(
            scalar=AsyncMock(return_value=0),
            execute=AsyncMock(return_value=rows),
        )

        await get_user_leagues(
            db=db,
            user_id=42,
            page=1,
            page_size=20,
            search="  rivals  ",
            sort_by="name",
            sort_order="asc",
        )

        count_query = db.scalar.await_args.args[0]
        self.assertIn("lower(leagues.name) LIKE lower", str(count_query))
        self.assertIn("%rivals%", count_query.compile().params.values())

    async def test_listing_includes_counts_and_last_scored_rank(self):
        now = datetime.now(timezone.utc)
        owner = SimpleNamespace(
            id=1,
            fpl_entry_id=100,
            role=LeagueMemberRole.OWNER,
            status=LeagueMemberStatus.APPROVED,
            joined_at=now,
            approved_at=now,
            scoring_start_gameweek=1,
        )
        active_league = SimpleNamespace(
            id=10,
            name="Active league",
            slug="active-league",
            status=LeagueStatus.ACTIVE,
        )
        draft_league = SimpleNamespace(
            id=20,
            name="Draft league",
            slug="draft-league",
            status=LeagueStatus.DRAFT,
        )
        approved_viewer = SimpleNamespace(
            id=2,
            status=LeagueMemberStatus.APPROVED,
        )
        pending_viewer = SimpleNamespace(
            id=3,
            status=LeagueMemberStatus.PENDING,
        )
        page_rows = Mock()
        page_rows.all.return_value = [
            (active_league, owner, approved_viewer, 8),
            (draft_league, owner, pending_viewer, 1),
        ]
        standing_rows = Mock()
        standing_rows.all.return_value = [
            SimpleNamespace(
                league_id=10,
                gameweek=6,
                league_member_id=2,
                rank=3,
            )
        ]
        db = SimpleNamespace(
            scalar=AsyncMock(return_value=2),
            execute=AsyncMock(side_effect=[page_rows, standing_rows]),
        )

        response = await get_user_leagues(
            db=db,
            user_id=42,
            page=1,
            page_size=20,
            search=None,
            sort_by="created_at",
            sort_order="desc",
        )

        active, draft = response.items
        self.assertEqual(active.member_count, 8)
        self.assertEqual(active.max_member_count, 20)
        self.assertEqual(active.last_scored_gameweek, 6)
        self.assertEqual(active.rank, 3)
        self.assertEqual(draft.member_count, 1)
        self.assertIsNone(draft.last_scored_gameweek)
        self.assertIsNone(draft.rank)
