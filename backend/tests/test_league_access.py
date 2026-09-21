from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from app.models.league import LeagueStatus
from app.models.league_member import (
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.schemas.league import LeagueUpdate
from app.services import gameweek
from app.services import league as league_service
from app.services.league_access import (
    LeagueMembershipPendingError,
    LeagueMembershipRequiredError,
    require_approved_league_member,
)


class LeagueAccessTests(IsolatedAsyncioTestCase):
    async def test_only_approved_members_are_allowed(self):
        for member, error in (
            (None, LeagueMembershipRequiredError),
            (
                SimpleNamespace(status=LeagueMemberStatus.PENDING),
                LeagueMembershipPendingError,
            ),
            (
                SimpleNamespace(status=LeagueMemberStatus.REJECTED),
                LeagueMembershipRequiredError,
            ),
        ):
            with self.subTest(member=member):
                db = SimpleNamespace(scalar=AsyncMock(return_value=member))

                with self.assertRaises(error):
                    await require_approved_league_member(
                        db=db,
                        league_id=1,
                        user_id=2,
                    )

        approved = SimpleNamespace(status=LeagueMemberStatus.APPROVED)
        db = SimpleNamespace(scalar=AsyncMock(return_value=approved))

        self.assertIs(
            await require_approved_league_member(
                db=db,
                league_id=1,
                user_id=2,
            ),
            approved,
        )

    async def test_gameweek_cache_is_not_read_before_authorization(self):
        db = SimpleNamespace(
            scalar=AsyncMock(return_value=SimpleNamespace(id=1))
        )

        with (
            patch.object(
                gameweek,
                "require_approved_league_member",
                new_callable=AsyncMock,
                side_effect=LeagueMembershipRequiredError,
            ),
            patch.object(
                gameweek,
                "get_cached_model",
                new_callable=AsyncMock,
            ) as get_cached,
        ):
            with self.assertRaises(LeagueMembershipRequiredError):
                await gameweek.get_league_gameweek(
                    db=db,
                    slug="private-league",
                    gameweek=1,
                    user_id=2,
                )

            get_cached.assert_not_awaited()

    async def test_league_member_visibility_depends_on_viewer_role(self):
        league = SimpleNamespace(
            id=1,
            name="Private league",
            slug="private-league",
            status=LeagueStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            started_at=None,
        )
        rules = SimpleNamespace(
            start_gameweek=1,
            include_transfer_deductions=True,
            allowed_chips=[],
        )

        for role, filters_by_status in (
            (LeagueMemberRole.OWNER, False),
            (LeagueMemberRole.MEMBER, True),
        ):
            with self.subTest(role=role):
                result = Mock()
                result.all.return_value = []
                db = SimpleNamespace(
                    scalar=AsyncMock(return_value=league),
                    execute=AsyncMock(return_value=result),
                )

                with (
                    patch.object(
                        league_service,
                        "require_approved_league_member",
                        new_callable=AsyncMock,
                        return_value=SimpleNamespace(role=role),
                    ),
                    patch.object(
                        league_service,
                        "_get_league_rules",
                        new_callable=AsyncMock,
                        return_value=rules,
                    ),
                    patch.object(
                        league_service,
                        "get_current_gameweek",
                        new_callable=AsyncMock,
                        return_value=5,
                    ),
                ):
                    await league_service.get_league(
                        db=db,
                        slug=league.slug,
                        user_id=2,
                    )

                query = str(db.execute.await_args.args[0])
                self.assertEqual(
                    "league_members.status =" in query,
                    filters_by_status,
                )

    async def test_league_members_include_fpl_names(self):
        now = datetime.now(timezone.utc)
        league = SimpleNamespace(
            id=1,
            name="Private league",
            slug="private-league",
            status=LeagueStatus.DRAFT,
            created_at=now,
            started_at=None,
        )
        member = SimpleNamespace(
            id=12,
            fpl_entry_id=4250337,
            role=LeagueMemberRole.OWNER,
            status=LeagueMemberStatus.APPROVED,
            joined_at=now,
            approved_at=now,
            scoring_start_gameweek=1,
        )
        account = SimpleNamespace(
            team_name="Rival XI FC",
            manager_name="Test Manager",
        )
        rules = SimpleNamespace(
            start_gameweek=1,
            include_transfer_deductions=True,
            allowed_chips=[],
        )
        result = Mock()
        result.all.return_value = [(member, account)]
        db = SimpleNamespace(
            scalar=AsyncMock(return_value=league),
            execute=AsyncMock(return_value=result),
        )

        with (
            patch.object(
                league_service,
                "require_approved_league_member",
                new_callable=AsyncMock,
                return_value=SimpleNamespace(role=LeagueMemberRole.OWNER),
            ),
            patch.object(
                league_service,
                "_get_league_rules",
                new_callable=AsyncMock,
                return_value=rules,
            ),
            patch.object(
                league_service,
                "get_current_gameweek",
                new_callable=AsyncMock,
                return_value=5,
            ),
        ):
            response = await league_service.get_league(
                db=db,
                slug=league.slug,
                user_id=2,
            )

        self.assertEqual(response.members[0].team_name, "Rival XI FC")
        self.assertEqual(response.members[0].manager_name, "Test Manager")
        self.assertEqual(response.current_gameweek, 5)

    async def test_updated_league_members_include_fpl_names(self):
        now = datetime.now(timezone.utc)
        league = SimpleNamespace(
            id=1,
            name="Private league",
            slug="private-league",
            status=LeagueStatus.DRAFT,
            created_at=now,
            started_at=None,
        )
        member = SimpleNamespace(
            id=12,
            fpl_entry_id=4250337,
            role=LeagueMemberRole.OWNER,
            status=LeagueMemberStatus.APPROVED,
            joined_at=now,
            approved_at=now,
            scoring_start_gameweek=1,
        )
        account = SimpleNamespace(
            team_name="Rival XI FC",
            manager_name="Test Manager",
        )
        rules = SimpleNamespace(
            start_gameweek=1,
            include_transfer_deductions=True,
            allowed_chips=[],
        )
        result = Mock()
        result.all.return_value = [(member, account)]
        transaction = Mock()
        transaction.__aenter__ = AsyncMock()
        transaction.__aexit__ = AsyncMock()
        db = SimpleNamespace(
            begin=Mock(return_value=transaction),
            execute=AsyncMock(return_value=result),
            flush=AsyncMock(),
            refresh=AsyncMock(),
        )

        with (
            patch.object(
                league_service,
                "_get_league_for_update",
                new_callable=AsyncMock,
                return_value=league,
            ),
            patch.object(
                league_service,
                "_require_owner",
                new_callable=AsyncMock,
            ),
            patch.object(
                league_service,
                "_get_league_rules",
                new_callable=AsyncMock,
                return_value=rules,
            ),
            patch.object(
                league_service,
                "get_current_gameweek",
                new_callable=AsyncMock,
                return_value=5,
            ),
        ):
            response = await league_service.update_league(
                db=db,
                slug=league.slug,
                data=LeagueUpdate(name=league.name),
                owner_user_id=2,
            )

        self.assertEqual(response.members[0].team_name, "Rival XI FC")
        self.assertEqual(response.members[0].manager_name, "Test Manager")
