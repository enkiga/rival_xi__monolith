import html

import httpx

from app.core.config import settings


class EmailDeliveryError(Exception):
    pass


def _email_html(body: str) -> str:
    paragraphs = "".join(
        f"<p>{html.escape(paragraph)}</p>"
        for paragraph in body.split("\n\n")
    )

    return (
        "<!doctype html>"
        '<html lang="en">'
        '<body style="font-family:Arial,sans-serif;line-height:1.5;'
        'color:#111827">'
        f"{paragraphs}"
        "</body>"
        "</html>"
    )


async def _send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    tag: str,
) -> None:
    if not settings.brevo_api_key:
        raise EmailDeliveryError("Brevo API key is not configured")

    if not settings.brevo_sender_email:
        raise EmailDeliveryError("Brevo sender is not configured")

    payload = {
        "sender": {
            "email": settings.brevo_sender_email,
            "name": settings.brevo_sender_name,
        },
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": body,
        "htmlContent": _email_html(body),
        "tags": [tag],
    }

    try:
        async with httpx.AsyncClient(
            base_url=settings.brevo_api_base_url,
            timeout=settings.brevo_timeout_seconds,
        ) as client:
            response = await client.post(
                "/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": settings.brevo_api_key,
                    "content-type": "application/json",
                },
                json=payload,
            )

        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Unable to send email through Brevo") from exc


async def send_auth_otp_email(
    *,
    email: str,
    code: str,
    expires_in_minutes: int,
) -> None:
    body = (
        f"Your Rivalxi verification code is: "
        f"{code}\n\n"
        f"This code expires in "
        f"{expires_in_minutes} minutes.\n\n"
        "If you did not request this code, "
        "you can ignore this email."
    )

    await _send_email(
        recipient=email,
        subject="Your Rivalxi verification code",
        body=body,
        tag="authentication",
    )


async def send_notification_email(
    *,
    email: str,
    subject: str,
    body: str,
) -> None:
    await _send_email(
        recipient=email,
        subject=subject,
        body=body,
        tag="notification",
    )
