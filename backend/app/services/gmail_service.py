from __future__ import annotations

import asyncio
import base64
import logging
import smtplib
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import Settings

logger = logging.getLogger(__name__)

GMAIL_SEND_SCOPE = ["https://www.googleapis.com/auth/gmail.send"]


class EmailSenderService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_email(self, to_email: str, subject: str, body: str, provider: str | None = None) -> str:
        provider_to_use = provider or self.settings.email_provider
        if provider_to_use == "smtp":
            return await asyncio.to_thread(self._send_via_smtp, to_email, subject, body)
        if provider_to_use == "gmail_api":
            return await asyncio.to_thread(self._send_via_gmail_api, to_email, subject, body)
        raise ValueError(f"Unsupported email provider: {provider_to_use}")

    def _build_message(self, to_email: str, subject: str, body: str) -> MIMEText:
        sender = self.settings.gmail_from_email or self.settings.gmail_smtp_user
        if not sender:
            raise ValueError("GMAIL_FROM_EMAIL or GMAIL_SMTP_USER must be configured.")
        message = MIMEText(body, "plain", "utf-8")
        message["To"] = to_email
        message["From"] = sender
        message["Subject"] = subject
        return message

    def _send_via_smtp(self, to_email: str, subject: str, body: str) -> str:
        user = self.settings.gmail_smtp_user
        app_password = self.settings.gmail_smtp_app_password
        if not user or not app_password:
            raise ValueError("SMTP requires GMAIL_SMTP_USER and GMAIL_SMTP_APP_PASSWORD.")

        message = self._build_message(to_email, subject, body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(user, app_password)
            server.sendmail(message["From"], [to_email], message.as_string())
        logger.info("Email sent via SMTP to %s", to_email)
        return f"smtp-{to_email}"

    def _send_via_gmail_api(self, to_email: str, subject: str, body: str) -> str:
        if not all(
            [
                self.settings.gmail_api_client_id,
                self.settings.gmail_api_client_secret,
                self.settings.gmail_api_refresh_token,
            ]
        ):
            raise ValueError(
                "Gmail API requires GMAIL_API_CLIENT_ID, GMAIL_API_CLIENT_SECRET, and "
                "GMAIL_API_REFRESH_TOKEN."
            )

        credentials = Credentials(
            token=None,
            refresh_token=self.settings.gmail_api_refresh_token,
            token_uri=self.settings.gmail_api_token_uri,
            client_id=self.settings.gmail_api_client_id,
            client_secret=self.settings.gmail_api_client_secret,
            scopes=GMAIL_SEND_SCOPE,
        )
        credentials.refresh(Request())

        service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

        message = self._build_message(to_email, subject, body)
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_result = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": encoded_message})
            .execute()
        )
        message_id = send_result.get("id", "")
        if not message_id:
            raise RuntimeError("Gmail API did not return a message id.")
        logger.info("Email sent via Gmail API to %s, id=%s", to_email, message_id)
        return message_id

