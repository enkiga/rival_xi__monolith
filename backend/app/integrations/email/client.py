import asyncio
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings


class EmailDeliveryError(Exception):
    pass


def _send_email(
    message: EmailMessage,
) -> None:
    if settings.smtp_host is None:
        raise EmailDeliveryError("SMTP host is not configured")

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=10,
        ) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls(context=ssl.create_default_context())

            if settings.smtp_username and settings.smtp_password:
                smtp.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            smtp.send_message(message)

    except EmailDeliveryError:
        raise

    except Exception as exc:
        raise EmailDeliveryError("Unable to send email") from exc


async def send_auth_otp_email(
    *,
    email: str,
    code: str,
    expires_in_minutes: int,
) -> None:
    if settings.smtp_from_email is None:
        raise EmailDeliveryError("SMTP sender is not configured")

    message = EmailMessage()

    message["Subject"] = "Your Rivalxi verification code"

    message["From"] = settings.smtp_from_email

    message["To"] = email

    message.set_content(
        f"Your Rivalxi verification code is: "
        f"{code}\n\n"
        f"This code expires in "
        f"{expires_in_minutes} minutes.\n\n"
        "If you did not request this code, "
        "you can ignore this email."
    )

    await asyncio.to_thread(
        _send_email,
        message,
    )


async def send_notification_email(
    *,
    email: str,
    subject: str,
    body: str,
) -> None:
    if settings.smtp_from_email is None:
        raise EmailDeliveryError("SMTP sender is not configured")

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = email

    message.set_content(body)

    await asyncio.to_thread(
        _send_email,
        message,
    )
