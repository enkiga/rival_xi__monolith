import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.integrations.email.client import (
    EmailDeliveryError,
    send_auth_otp_email,
    send_notification_email,
)


class EmailClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_sends_otp_through_brevo(self):
        response = MagicMock()
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response

        context = AsyncMock()
        context.__aenter__.return_value = client

        with (
            patch("app.integrations.email.client.settings") as settings,
            patch(
                "app.integrations.email.client.httpx.AsyncClient",
                return_value=context,
            ),
        ):
            settings.brevo_api_key = "test-api-key"
            settings.brevo_sender_email = "no-reply@example.com"
            settings.brevo_sender_name = "RivalXI"
            settings.brevo_api_base_url = "https://api.brevo.com"
            settings.brevo_timeout_seconds = 10.0

            await send_auth_otp_email(
                email="manager@example.com",
                code="123456",
                expires_in_minutes=10,
            )

        request = client.post.await_args

        self.assertEqual(request.args[0], "/v3/smtp/email")
        self.assertEqual(request.kwargs["headers"]["api-key"], "test-api-key")
        self.assertEqual(
            request.kwargs["json"]["sender"],
            {
                "email": "no-reply@example.com",
                "name": "RivalXI",
            },
        )
        self.assertEqual(
            request.kwargs["json"]["to"],
            [{"email": "manager@example.com"}],
        )
        self.assertIn("123456", request.kwargs["json"]["textContent"])
        self.assertNotIn("123456", request.kwargs["json"]["subject"])

    async def test_requires_api_key(self):
        with patch("app.integrations.email.client.settings") as settings:
            settings.brevo_api_key = None

            with self.assertRaisesRegex(EmailDeliveryError, "API key"):
                await send_notification_email(
                    email="manager@example.com",
                    subject="Membership approved",
                    body="You are in.",
                )

    async def test_wraps_brevo_http_errors(self):
        client = AsyncMock()
        client.post.side_effect = httpx.ConnectError("connection failed")

        context = AsyncMock()
        context.__aenter__.return_value = client

        with (
            patch("app.integrations.email.client.settings") as settings,
            patch(
                "app.integrations.email.client.httpx.AsyncClient",
                return_value=context,
            ),
        ):
            settings.brevo_api_key = "test-api-key"
            settings.brevo_sender_email = "no-reply@example.com"
            settings.brevo_sender_name = "RivalXI"
            settings.brevo_api_base_url = "https://api.brevo.com"
            settings.brevo_timeout_seconds = 10.0

            with self.assertRaises(EmailDeliveryError):
                await send_notification_email(
                    email="manager@example.com",
                    subject="Membership approved",
                    body="You are in.",
                )
