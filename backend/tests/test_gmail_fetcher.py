"""Tests for Gmail fetcher module."""

import base64
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gmail_fetcher import GmailFetcher


def _make_message(subject, date, html_body, msg_id="msg123"):
    """Build a Gmail API message dict with the given subject, date, and HTML body."""
    encoded = base64.urlsafe_b64encode(html_body.encode()).decode()
    return {
        "id": msg_id,
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": date},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"plain text").decode()},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": encoded},
                },
            ],
        },
    }


class TestExtractHtmlFromMessage:
    def test_simple_html(self):
        msg = _make_message("Test", "Mon, 01 Jan 2024 00:00:00 GMT", "<p>Hello</p>")
        result = GmailFetcher._extract_html_from_message(msg["payload"])
        assert result == "<p>Hello</p>"

    def test_no_html_part(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": base64.urlsafe_b64encode(b"plain only").decode()},
        }
        result = GmailFetcher._extract_html_from_message(payload)
        assert result is None

    def test_nested_multipart(self):
        encoded = base64.urlsafe_b64encode(b"<div>Nested</div>").decode()
        payload = {
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "multipart/alternative",
                    "parts": [
                        {"mimeType": "text/plain", "body": {"data": "cGxhaW4="}},
                        {"mimeType": "text/html", "body": {"data": encoded}},
                    ],
                }
            ],
        }
        result = GmailFetcher._extract_html_from_message(payload)
        assert result == "<div>Nested</div>"


class TestExtractCanonicalUrl:
    def test_latent_space_url(self):
        html = '<a href="https://www.latent.space/p/ainews-title-here">View in browser</a>'
        assert GmailFetcher._extract_canonical_url(html) == "https://www.latent.space/p/ainews-title-here"

    def test_url_with_query_params_stripped(self):
        html = '<a href="https://www.latent.space/p/some-post?utm_source=email">View</a>'
        assert GmailFetcher._extract_canonical_url(html) == "https://www.latent.space/p/some-post"

    def test_no_latent_space_url(self):
        html = "<p>No links here</p>"
        assert GmailFetcher._extract_canonical_url(html) is None

    def test_fallback_bare_url(self):
        html = 'Check out https://www.latent.space/p/my-post for more'
        assert GmailFetcher._extract_canonical_url(html) == "https://www.latent.space/p/my-post"


class TestStripEmailWrapper:
    def test_with_post_body_div(self):
        html = '<html><body><table><tr><td><div class="post-body"><p>Content</p></div></td></tr></table></body></html>'
        result = GmailFetcher._strip_email_wrapper(html)
        assert "Content" in result
        # Should not contain the outer table structure
        assert "<table>" not in result

    def test_fallback_largest_td(self):
        long_content = "x" * 600
        html = f'<html><body><table><tr><td>Short</td></tr><tr><td>{long_content}</td></tr></table></body></html>'
        result = GmailFetcher._strip_email_wrapper(html)
        assert long_content in result

    def test_no_wrapper_returns_full(self):
        html = "<p>Simple content</p>"
        result = GmailFetcher._strip_email_wrapper(html)
        assert "Simple content" in result


class TestSubjectFiltering:
    @patch("gmail_fetcher.build")
    def test_title_filter_skips_non_matching(self, mock_build):
        service = MagicMock()
        mock_build.return_value = service

        msg_list = {"messages": [{"id": "1"}, {"id": "2"}]}
        service.users().messages().list().execute.return_value = msg_list

        msg_no_match = _make_message(
            "Latent Space Podcast Episode 5",
            "Mon, 01 Jan 2024 00:00:00 GMT",
            '<p>Not ainews</p><a href="https://www.latent.space/p/podcast-5">View</a>',
            "1",
        )
        msg_match = _make_message(
            "[AINews] The Big Update",
            "Tue, 02 Jan 2024 00:00:00 GMT",
            '<p>AINews content</p><a href="https://www.latent.space/p/ainews-big-update">View</a>',
            "2",
        )

        service.users().messages().get().execute.side_effect = [msg_no_match, msg_match]

        fetcher = GmailFetcher("id", "secret", "token")
        result = fetcher.fetch_latest_email(
            "swyx+ainews@substack.com", title_filter=r"^\[AINews\]", entry_index=0
        )

        assert result is not None
        url, title, html, published = result
        assert title == "[AINews] The Big Update"
        assert "ainews-big-update" in url

    @patch("gmail_fetcher.build")
    def test_entry_index_skips_earlier_matches(self, mock_build):
        service = MagicMock()
        mock_build.return_value = service

        msg_list = {"messages": [{"id": "1"}, {"id": "2"}]}
        service.users().messages().list().execute.return_value = msg_list

        msg1 = _make_message(
            "[AINews] Latest",
            "Tue, 02 Jan 2024 00:00:00 GMT",
            '<p>New</p><a href="https://www.latent.space/p/latest">View</a>',
            "1",
        )
        msg2 = _make_message(
            "[AINews] Older",
            "Mon, 01 Jan 2024 00:00:00 GMT",
            '<p>Old</p><a href="https://www.latent.space/p/older">View</a>',
            "2",
        )

        service.users().messages().get().execute.side_effect = [msg1, msg2]

        fetcher = GmailFetcher("id", "secret", "token")
        result = fetcher.fetch_latest_email(
            "swyx+ainews@substack.com", title_filter=r"^\[AINews\]", entry_index=1
        )

        assert result is not None
        _, title, _, _ = result
        assert title == "[AINews] Older"


class TestProcessorGmailIntegration:
    """Test processor routing to Gmail fetcher."""

    @pytest.mark.asyncio
    async def test_fetch_routes_to_gmail(self, processor):
        """ainews source with fetchMethod=gmail should call _fetch_from_gmail."""
        proc = processor
        mock_result = (
            "https://www.latent.space/p/test",
            "[AINews] Test",
            "<p>Content</p>",
            "2024-01-01T00:00:00",
            "ainews",
        )

        with patch.object(proc, "_fetch_from_gmail", new_callable=AsyncMock, return_value=mock_result) as mock_gmail:
            result = await proc.fetch_latest_newsletter(entry_index=0, source_id="ainews")

        assert result == mock_result
        mock_gmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_gmail_fetcher_not_configured(self, processor):
        """Missing Gmail credentials should return None gracefully."""
        proc = processor

        with patch.dict(os.environ, {}, clear=True):
            result = await proc._fetch_from_gmail(
                {"gmail": {"senderEmail": "test@example.com"}, "titleFilter": None},
                entry_index=0,
                source_id="ainews",
            )

        assert result is None
