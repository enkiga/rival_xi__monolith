from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from app.jobs import gameweek as gameweek_job
from app.models.gameweek_result import GameweekResultStatus
from app.models.league import LeagueStatus
from app.models.league_member import (
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.models.notification import NotificationType
from app.services import gameweek, league, notification


class AsyncContext:
    def __init__(
        self,
        on_enter=None,
        on_exit=None,
        return_value=None,
    ):
        self.on_enter = on_enter
        self.on_exit = on_exit
        self.return_value = return_value

    async def __aenter__(self):
        if self.on_enter is not None:
            self.on_enter()

        return self.return_value or self

    async def __aexit__(self, exc_type, exc, traceback):
        if self.on_exit is not None:
            self.on_exit()


class NotificationEventTests(IsolatedAsyncioTestCase):
    async def test_retryable_event_helpers_set_dedupe_keys(self):
        db = object()

        with patch.object(
            notification,
            "create_notification",
            new_callable=AsyncMock,
        ) as create:
            await notification.notify_gameweek_winner(
                db=db,
                user_id=7,
                league_id=3,
                league_slug="rivals",
                gameweek=12,
                body="Rivals won.",
            )
            self.assertEqual(
                create.await_args.kwargs["type"],
                NotificationType.GAMEWEEK_WINNER,
            )
            self.assertEqual(
                create.await_args.kwargs["dedupe_key"],
                "gw-winner:3:12:7",
            )

            await notification.notify_fpl_deadline(
                db=db,
                user_id=7,
                gameweek=13,
                deadline_time="2026-09-20T10:00:00Z",
            )
            self.assertEqual(
                create.await_args.kwargs["type"],
                NotificationType.FPL_DEADLINE,
            )
            self.assertEqual(
                create.await_args.kwargs["dedupe_key"],
                "fpl-deadline:13:7",
            )

    async def test_approval_email_runs_after_transaction(self):
        transaction_active = False

        def enter_transaction():
            nonlocal transaction_active
            transaction_active = True

        def exit_transaction():
            nonlocal transaction_active
            transaction_active = False

        db = SimpleNamespace(
            begin=lambda: AsyncContext(
                enter_transaction,
                exit_transaction,
            ),
            scalar=AsyncMock(),
            flush=AsyncMock(),
            refresh=AsyncMock(),
        )
        member = SimpleNamespace(
            id=4,
            user_id=9,
            fpl_entry_id=100,
            role=LeagueMemberRole.MEMBER,
            status=LeagueMemberStatus.PENDING,
            joined_at=datetime.now(timezone.utc),
            approved_at=None,
            scoring_start_gameweek=None,
        )
        db.scalar.side_effect = [member, 1]
        league_record = SimpleNamespace(
            id=2,
            slug="rivals",
            name="Rivals",
            status=LeagueStatus.DRAFT,
        )
        rules = SimpleNamespace(start_gameweek=1)

        async def notify(**kwargs):
            self.assertTrue(transaction_active)
            return SimpleNamespace(id=15)

        async def deliver(notification_id):
            self.assertFalse(transaction_active)
            self.assertEqual(notification_id, 15)
            return True

        with (
            patch.object(
                league,
                "get_current_gameweek",
                new=AsyncMock(return_value=2),
            ),
            patch.object(
                league,
                "_get_league_for_update",
                new=AsyncMock(return_value=league_record),
            ),
            patch.object(
                league,
                "_require_owner",
                new_callable=AsyncMock,
            ),
            patch.object(
                league,
                "_get_league_rules",
                new=AsyncMock(return_value=rules),
            ),
            patch.object(
                league,
                "notify_membership_approved",
                new=AsyncMock(side_effect=notify),
            ),
            patch.object(
                league,
                "deliver_notification_email",
                new=AsyncMock(side_effect=deliver),
            ),
        ):
            response = await league.approve_league_member(
                db=db,
                slug="rivals",
                member_id=member.id,
                owner_user_id=1,
            )

        self.assertEqual(response.status, LeagueMemberStatus.APPROVED)

    async def test_winner_notification_supports_ties_and_all_recipients(self):
        winner_rows = Mock()
        winner_rows.all.return_value = [
            (1, 101, "Alpha"),
            (2, 102, "Beta"),
        ]
        recipient_rows = Mock()
        recipient_rows.scalars.return_value.all.return_value = [7, 8, 9]
        db = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[winner_rows, recipient_rows]
            )
        )
        winners = [
            SimpleNamespace(
                eligible=True,
                rank=1,
                league_member_id=1,
                fpl_entry_id=101,
                scoreboard_points=50,
            ),
            SimpleNamespace(
                eligible=True,
                rank=1,
                league_member_id=2,
                fpl_entry_id=102,
                scoreboard_points=50,
            ),
        ]

        with (
            patch.object(
                gameweek,
                "_get_gameweek_result_rows",
                new=AsyncMock(return_value=[object()]),
            ),
            patch.object(
                gameweek,
                "_rank_results",
                return_value=winners,
            ),
            patch.object(
                gameweek,
                "notify_gameweek_winner",
                new_callable=AsyncMock,
            ) as notify,
        ):
            await gameweek._create_gameweek_winner_notifications(
                db=db,
                league_id=5,
                league_slug="rivals",
                gameweek=6,
            )

        self.assertEqual(notify.await_count, 3)
        self.assertEqual(
            notify.await_args_list[0].kwargs["body"],
            "Alpha and Beta tied for Gameweek 6 with 50 points.",
        )

    async def test_deadline_job_targets_users_in_reminder_window(self):
        deadline = datetime.now(timezone.utc) + timedelta(hours=12)
        bootstrap = {
            "events": [
                {
                    "id": 8,
                    "is_next": True,
                    "deadline_time": deadline.isoformat(),
                }
            ]
        }
        result = Mock()
        result.scalars.return_value.all.return_value = [3, 4]
        read_db = SimpleNamespace(execute=AsyncMock(return_value=result))
        write_db = SimpleNamespace(begin=lambda: AsyncContext())
        sessions = [
            AsyncContext(return_value=read_db),
            AsyncContext(return_value=write_db),
        ]

        session_factory = Mock(side_effect=sessions)

        with (
            patch.object(
                gameweek_job,
                "get_bootstrap_static",
                new=AsyncMock(return_value=bootstrap),
            ),
            patch.object(
                gameweek_job,
                "AsyncSessionLocal",
                session_factory,
            ),
            patch.object(
                gameweek_job,
                "notify_fpl_deadline",
                new_callable=AsyncMock,
            ) as notify,
        ):
            await gameweek_job.run_deadline_reminder_job()

        self.assertEqual(notify.await_count, 2)
        self.assertEqual(
            [call.kwargs["user_id"] for call in notify.await_args_list],
            [3, 4],
        )
        self.assertIn(
            "SELECT DISTINCT",
            str(read_db.execute.await_args.args[0]),
        )
