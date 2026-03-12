"""Gmail API fetcher for newsletter emails."""

import base64
import logging
import re
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailFetcher:
    """Fetches newsletter emails via the Gmail API using OAuth2 refresh token."""

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri=TOKEN_URI,
        )
        self.service = build("gmail", "v1", credentials=creds)

    def fetch_latest_email(
        self,
        sender_email: str,
        title_filter: str | None = None,
        entry_index: int = 0,
    ) -> tuple[str, str, str, str | None] | None:
        """Fetch a newsletter email from Gmail.

        Args:
            sender_email: Email address to filter by (from: query).
            title_filter: Optional regex to match against subject lines.
            entry_index: 0 = newest matching email, 1 = second newest, etc.

        Returns:
            (url, title, html_content, published_iso) or None if not found.
        """
        query = f"from:{sender_email}"
        # Fetch enough messages to skip past non-matching subjects
        max_results = (entry_index + 1) * 5
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            logger.warning(f"No emails found from {sender_email}")
            return None

        match_count = 0
        for msg_stub in messages:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_stub["id"], format="full")
                .execute()
            )

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "")
            date_str = headers.get("Date")

            # Apply title filter
            if title_filter and not re.search(title_filter, subject):
                continue

            if match_count < entry_index:
                match_count += 1
                continue

            # Extract HTML body
            html_content = self._extract_html_from_message(msg["payload"])
            if not html_content:
                logger.warning(f"No HTML content in email: {subject}")
                continue

            # Extract canonical URL from email HTML
            url = self._extract_canonical_url(html_content)
            if not url:
                # Fallback: use a constructed URL from subject
                url = f"gmail://msg/{msg_stub['id']}"
                logger.info(f"No canonical URL found, using fallback: {url}")

            # Parse date
            published = None
            if date_str:
                try:
                    published = parsedate_to_datetime(date_str).isoformat()
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse email date: {date_str}")

            # Strip Substack email wrapper, keep newsletter body
            html_content = self._strip_email_wrapper(html_content)

            logger.info(
                f"Found email #{entry_index}: {subject} ({len(html_content)} chars)"
            )
            return (url, subject, html_content, published)

        logger.warning(
            f"No matching email at index {entry_index} from {sender_email} "
            f"(found {match_count} matches)"
        )
        return None

    @staticmethod
    def _extract_html_from_message(payload: dict) -> str | None:
        """Recursively extract text/html content from a Gmail message payload."""
        mime_type = payload.get("mimeType", "")

        if mime_type == "text/html":
            data = payload.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")

        # Recurse into multipart parts
        for part in payload.get("parts", []):
            result = GmailFetcher._extract_html_from_message(part)
            if result:
                return result

        return None

    @staticmethod
    def _extract_canonical_url(html: str) -> str | None:
        """Extract the canonical newsletter URL from Substack email HTML.

        Substack emails wrap links in redirects like:
        https://substack.com/redirect/2/<base64-jwt>
        The JWT payload contains an "e" field with the actual destination URL.
        Falls back to direct latent.space/p/ links if found.
        """
        import json

        # Strategy 1: Decode Substack redirect tokens for latent.space/p/ URLs
        # Format: substack.com/redirect/2/<base64-payload>.<signature>
        redirects = re.findall(r'https://substack\.com/redirect/2/([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', html)
        for token in redirects:
            try:
                payload_b64 = token.split(".")[0]
                # Add padding
                padding = 4 - len(payload_b64) % 4
                if padding != 4:
                    payload_b64 += "=" * padding
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                dest_url = payload.get("e", "")
                if "latent.space/p/" in dest_url:
                    # Strip query params
                    clean_url = dest_url.split("?")[0]
                    return clean_url
            except Exception:
                continue

        # Strategy 2: Direct latent.space/p/ link
        direct = re.search(
            r'<a[^>]+href="(https?://[^"]*latent\.space/p/[^"?]*)',
            html,
        )
        if direct:
            return direct.group(1)

        # Strategy 3: Bare URL in text
        bare = re.search(
            r'https?://[^"\s]*latent\.space/p/[^"?\s]*',
            html,
        )
        if bare:
            return bare.group(0)

        return None

    @staticmethod
    def _strip_email_wrapper(html: str) -> str:
        """Strip Substack email wrapper tables, keeping the newsletter body.

        Substack emails wrap content in nested tables. The actual newsletter
        content lives inside a div or td with the post body. If we can't
        find a clean boundary, return the full HTML (the parser will handle it).
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # Substack emails use a specific post body container
        # Try common Substack email content selectors
        for selector in [
            "div.email-body-content",
            "div.post-body",
            "div.body",
            "td.post-body",
        ]:
            body = soup.select_one(selector)
            if body:
                return str(body)

        # Fallback: look for the main content table cell with substantial content
        # Substack emails have the content in a deeply nested td
        candidates = soup.find_all("td")
        best = None
        best_len = 0
        for td in candidates:
            # Skip tiny cells (navigation, footer, etc.)
            text_len = len(td.get_text(strip=True))
            if text_len > best_len:
                best = td
                best_len = text_len

        if best and best_len > 500:
            return str(best)

        # Return full HTML if we can't isolate the body
        return html
