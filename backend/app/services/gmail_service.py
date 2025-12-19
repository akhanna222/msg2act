"""
Gmail service for fetching and syncing emails
"""
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from email.utils import parsedate_to_datetime
import email

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.security import decrypt_token
from app.models.oauth_token import OAuthToken
from app.models.data_source import DataSource
from app.models.message import Message
from app.core.config import settings


class GmailService:
    """Service for interacting with Gmail API"""

    def __init__(self, oauth_token: OAuthToken):
        """
        Initialize Gmail service with OAuth credentials

        Args:
            oauth_token: OAuthToken model instance with encrypted tokens
        """
        self.oauth_token = oauth_token

        # Decrypt tokens
        access_token = decrypt_token(oauth_token.access_token)
        refresh_token = decrypt_token(oauth_token.refresh_token) if oauth_token.refresh_token else None

        # Create credentials
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES,
        )

        # Build Gmail API client
        self.service = build("gmail", "v1", credentials=self.credentials)

    def fetch_messages(
        self,
        max_results: int = 100,
        after_date: Optional[datetime] = None,
        query: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch messages from Gmail

        Args:
            max_results: Maximum number of messages to fetch
            after_date: Only fetch messages after this date
            query: Gmail search query (e.g., "is:unread", "from:example@email.com")

        Returns:
            List of message dictionaries
        """
        try:
            # Build query
            search_query = query or ""

            if after_date:
                # Gmail uses format YYYY/MM/DD
                date_str = after_date.strftime("%Y/%m/%d")
                search_query = f"{search_query} after:{date_str}".strip()

            # List messages
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=search_query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            # Fetch full message details
            full_messages = []
            for msg in messages:
                try:
                    full_msg = self.get_message(msg["id"])
                    if full_msg:
                        full_messages.append(full_msg)
                except Exception as e:
                    print(f"Error fetching message {msg['id']}: {e}")
                    continue

            return full_messages

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_message(self, message_id: str) -> Optional[Dict]:
        """
        Get full message details

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with message details
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            return self.parse_message(message)

        except HttpError as error:
            print(f"Error getting message {message_id}: {error}")
            return None

    def parse_message(self, message: Dict) -> Dict:
        """
        Parse Gmail API message into our format

        Args:
            message: Gmail API message object

        Returns:
            Dictionary with parsed message data
        """
        headers = message["payload"].get("headers", [])

        # Extract headers
        subject = self._get_header(headers, "Subject")
        from_email = self._get_header(headers, "From")
        to = self._get_header(headers, "To")
        cc = self._get_header(headers, "Cc")
        date = self._get_header(headers, "Date")

        # Parse from email (format: "Name <email@example.com>")
        from_name, from_email_addr = self._parse_email_address(from_email)

        # Parse recipients
        to_emails = self._parse_email_list(to)
        cc_emails = self._parse_email_list(cc)

        # Get message body
        body_text, body_html = self._get_body(message["payload"])

        # Parse date
        received_at = None
        if date:
            try:
                received_at = parsedate_to_datetime(date)
            except Exception:
                received_at = datetime.utcnow()

        # Check for attachments
        has_attachments = self._has_attachments(message["payload"])

        return {
            "external_id": message["id"],
            "thread_id": message.get("threadId"),
            "subject": subject,
            "from_email": from_email_addr,
            "from_name": from_name,
            "to_emails": to_emails,
            "cc_emails": cc_emails,
            "body_text": body_text,
            "body_html": body_html,
            "received_at": received_at,
            "has_attachments": has_attachments,
            "labels": message.get("labelIds", []),
            "raw_metadata": {
                "snippet": message.get("snippet"),
                "internal_date": message.get("internalDate"),
            },
        }

    def _get_header(self, headers: List[Dict], name: str) -> Optional[str]:
        """Get header value by name"""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return None

    def _parse_email_address(self, email_str: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Parse email address from "Name <email@example.com>" format

        Returns:
            Tuple of (name, email)
        """
        if not email_str:
            return None, None

        # Try to parse "Name <email@example.com>" format
        if "<" in email_str and ">" in email_str:
            name = email_str.split("<")[0].strip().strip('"')
            email_addr = email_str.split("<")[1].split(">")[0].strip()
            return name, email_addr

        # Just an email address
        return None, email_str.strip()

    def _parse_email_list(self, email_str: Optional[str]) -> List[str]:
        """Parse comma-separated list of email addresses"""
        if not email_str:
            return []

        emails = []
        for addr in email_str.split(","):
            _, email_addr = self._parse_email_address(addr.strip())
            if email_addr:
                emails.append(email_addr)

        return emails

    def _get_body(self, payload: Dict) -> tuple[Optional[str], Optional[str]]:
        """
        Extract message body (both text and HTML)

        Returns:
            Tuple of (plain_text, html)
        """
        text_body = None
        html_body = None

        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                mime_type = part.get("mimeType")

                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    text_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

                elif mime_type == "text/html" and "data" in part.get("body", {}):
                    html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")

                elif "parts" in part:
                    # Nested parts
                    nested_text, nested_html = self._get_body(part)
                    if not text_body:
                        text_body = nested_text
                    if not html_body:
                        html_body = nested_html

        elif "body" in payload and "data" in payload["body"]:
            # Simple message
            mime_type = payload.get("mimeType")
            data = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

            if mime_type == "text/plain":
                text_body = data
            elif mime_type == "text/html":
                html_body = data

        return text_body, html_body

    def _has_attachments(self, payload: Dict) -> bool:
        """Check if message has attachments"""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    return True
                if "parts" in part:
                    if self._has_attachments(part):
                        return True
        return False

    def get_attachment(self, message_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download attachment

        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID

        Returns:
            Attachment data as bytes
        """
        try:
            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            data = attachment["data"]
            return base64.urlsafe_b64decode(data)

        except HttpError as error:
            print(f"Error downloading attachment: {error}")
            return None
