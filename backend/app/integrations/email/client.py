import html
from urllib.parse import quote

import httpx

from app.core.config import settings


class EmailDeliveryError(Exception):
    pass


def _logo_url() -> str:
    return (
        f"{settings.frontend_base_url.rstrip('/')}"
        "/email-assets/rivalxi-logo.png"
    )


def _email_layout(*, preview: str, content: str) -> str:
    logo_url = html.escape(_logo_url(), quote=True)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<style>
@media only screen and (max-width:620px) {{
  .card {{ width:100% !important; }}
  .pad {{ padding-left:24px !important; padding-right:24px !important; }}
  .heading {{ font-size:32px !important; line-height:38px !important; }}
}}
</style>
</head>
<body style="margin:0;background:#f3f1fb;font-family:Arial,Helvetica,sans-serif;color:#10101c">
<div style="display:none;max-height:0;overflow:hidden">{html.escape(preview)}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f3f1fb">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" class="card" width="600" cellspacing="0" cellpadding="0" border="0" style="width:600px;max-width:600px;background:#fff;border-radius:8px;overflow:hidden">
<tr><td class="pad" style="padding:30px 40px;background:#19072f">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"><tr>
<td><img src="{logo_url}" width="180" alt="RivalXI" style="display:block;width:180px;max-width:100%;height:auto;border:0"></td>
<td align="right" style="color:#d8d1e4;font-size:14px;line-height:21px">Play With Friends.<br>Win Every Week.</td>
</tr></table>
</td></tr>
{content}
<tr><td class="pad" style="padding:28px 40px;background:#111024">
<img src="{logo_url}" width="132" alt="RivalXI" style="display:block;width:132px;height:auto;border:0;margin-bottom:12px">
<p style="margin:0;color:#aaa6bc;font-size:14px;line-height:21px">A private FPL league platform for friends.</p>
</td></tr>
</table>
</td></tr></table>
</body>
</html>"""


def _league_card(
    *,
    league_name: str,
    member_count: int,
    max_member_count: int,
) -> str:
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f7f6fc;border-radius:10px">
<tr>
<td width="58" style="padding:18px 0 18px 18px;color:#5a20bc;font-size:32px;line-height:40px">&#9819;</td>
<td style="padding:18px">
<p style="margin:0 0 5px;font-size:18px;line-height:24px;font-weight:700">{html.escape(league_name)}</p>
<p style="margin:0;color:#676378;font-size:14px;line-height:20px">Invite-only &nbsp;&bull;&nbsp; {member_count} / {max_member_count} members</p>
</td>
</tr>
</table>"""


def _otp_email_html(*, code: str, expires_in_minutes: int) -> str:
    content = f"""
<tr><td class="pad" style="padding:46px 44px 52px">
<p style="margin:0 0 22px;color:#7770b5;font-size:13px;font-weight:700;letter-spacing:4px;text-transform:uppercase">Security</p>
<h1 class="heading" style="margin:0 0 26px;font-size:40px;line-height:47px">Your RivalXI<br>verification code</h1>
<p style="margin:0 0 28px;color:#555166;font-size:17px;line-height:26px">Use the code below to sign in to your RivalXI account.<br>This code will expire in {expires_in_minutes} minutes.</p>
<div style="margin-bottom:28px;padding:30px 20px;background:#f4f2fc;border-radius:10px;text-align:center;font-size:38px;font-weight:700;letter-spacing:12px">{html.escape(code)}</div>
<p style="margin:0 0 28px;color:#10101c;font-size:16px;line-height:24px"><strong>Expires in <span style="color:#5426d6">{expires_in_minutes} minutes</span></strong><br><span style="color:#676378;font-size:14px">For your security, this code can only be used once.</span></p>
<div style="border-top:1px solid #e3e0ee;padding-top:28px">
<div style="padding:20px;background:#f4f2fc;border-radius:10px">
<p style="margin:0 0 4px;font-size:16px;line-height:23px;font-weight:700">Didn&rsquo;t request this code?</p>
<p style="margin:0;color:#676378;font-size:14px;line-height:21px">If you did not request this code, you can safely ignore this email. Your account remains secure.</p>
</div>
</div>
</td></tr>"""
    return _email_layout(
        preview="Your RivalXI verification code",
        content=content,
    )


def _membership_email_html(
    *,
    approved: bool,
    league_name: str,
    league_slug: str,
    member_count: int,
    max_member_count: int,
) -> str:
    safe_name = html.escape(league_name)
    league_card = _league_card(
        league_name=league_name,
        member_count=member_count,
        max_member_count=max_member_count,
    )

    if approved:
        league_url = (
            f"{settings.frontend_base_url.rstrip('/')}"
            f"/league/{quote(league_slug, safe='')}"
        )
        safe_url = html.escape(league_url, quote=True)
        main_content = f"""
<p style="margin:0 0 22px;color:#7770b5;font-size:13px;font-weight:700;letter-spacing:4px;text-transform:uppercase">Membership approved</p>
<h1 class="heading" style="margin:0 0 26px;font-size:40px;line-height:47px">You&rsquo;ve been approved<br>to join {safe_name}!</h1>
<p style="margin:0 0 28px;color:#555166;font-size:17px;line-height:26px">Great news! A league owner has approved your request.<br>You&rsquo;re now a member and can start competing.</p>
{league_card}
<div style="margin:28px 0 32px;border-radius:9px;background:#6336ee;text-align:center"><a href="{safe_url}" style="display:block;padding:16px 24px;color:#fff;font-size:17px;font-weight:700;text-decoration:none">View league &nbsp;&rarr;</a></div>
<div style="border-top:1px solid #e3e0ee;padding-top:28px">
<h2 style="margin:0 0 18px;font-size:20px">What&rsquo;s next?</h2>
<p style="margin:0 0 14px;line-height:23px"><strong>Check the current standings</strong><br><span style="color:#676378;font-size:14px">See how everyone is doing this gameweek.</span></p>
<p style="margin:0 0 14px;line-height:23px"><strong>Explore your league</strong><br><span style="color:#676378;font-size:14px">View members, rules and past results.</span></p>
<p style="margin:0;line-height:23px"><strong>Show off your squad</strong><br><span style="color:#676378;font-size:14px">Compare teams and see what others are playing.</span></p>
</div>"""
        preview = f"You've been approved to join {league_name}"
    else:
        main_content = f"""
<p style="margin:0 0 22px;color:#7770b5;font-size:13px;font-weight:700;letter-spacing:4px;text-transform:uppercase">Membership update</p>
<h1 class="heading" style="margin:0 0 26px;font-size:40px;line-height:47px">Your request to join<br>{safe_name} was<br>not approved</h1>
<p style="margin:0 0 28px;color:#555166;font-size:17px;line-height:26px">A league owner has reviewed your request and decided not to approve it at this time.</p>
{league_card}
<div style="margin-top:28px;padding:20px;background:#fff0f2;border-radius:10px">
<p style="margin:0 0 4px;color:#8f1233;font-size:16px;line-height:23px;font-weight:700">What does this mean?</p>
<p style="margin:0;color:#7a4755;font-size:14px;line-height:21px">You&rsquo;re currently not a member of this league, so you won&rsquo;t be able to view the league or its content.</p>
</div>"""
        preview = f"Your request to join {league_name} was not approved"

    return _email_layout(
        preview=preview,
        content=(
            '<tr><td class="pad" style="padding:46px 44px 52px">'
            f"{main_content}</td></tr>"
        ),
    )


async def _send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    html_content: str,
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
        "htmlContent": html_content,
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
        f"Your RivalXI verification code is: {code}\n\n"
        f"This code expires in {expires_in_minutes} minutes.\n\n"
        "If you did not request this code, you can ignore this email."
    )

    await _send_email(
        recipient=email,
        subject="Your RivalXI verification code",
        body=body,
        html_content=_otp_email_html(
            code=code,
            expires_in_minutes=expires_in_minutes,
        ),
        tag="authentication",
    )


async def send_notification_email(
    *,
    email: str,
    subject: str,
    approved: bool,
    league_name: str,
    league_slug: str,
    member_count: int,
    max_member_count: int,
) -> None:
    if approved:
        league_url = (
            f"{settings.frontend_base_url.rstrip('/')}"
            f"/league/{quote(league_slug, safe='')}"
        )
        body = (
            f"You've been approved to join {league_name}!\n\n"
            "Great news! A league owner has approved your request. "
            "You're now a member and can start competing.\n\n"
            f"Invite-only · {member_count} / {max_member_count} members\n\n"
            f"View league: {league_url}\n\n"
            "What's next?\n"
            "- Check the current standings\n"
            "- Explore your league\n"
            "- Show off your squad"
        )
    else:
        body = (
            f"Your request to join {league_name} was not approved.\n\n"
            "A league owner has reviewed your request and decided not to "
            "approve it at this time.\n\n"
            f"Invite-only · {member_count} / {max_member_count} members\n\n"
            "You're currently not a member of this league, so you won't be "
            "able to view the league or its content."
        )

    await _send_email(
        recipient=email,
        subject=subject,
        body=body,
        html_content=_membership_email_html(
            approved=approved,
            league_name=league_name,
            league_slug=league_slug,
            member_count=member_count,
            max_member_count=max_member_count,
        ),
        tag="notification",
    )
