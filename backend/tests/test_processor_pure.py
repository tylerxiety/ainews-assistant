"""Unit tests for pure/static functions in NewsletterProcessor."""
import pytest

from processor import NewsletterProcessor


# ────────────────────────────────────────────
# _normalize_extracted_text (staticmethod)
# ────────────────────────────────────────────

class TestNormalizeExtractedText:
    def test_collapses_whitespace(self):
        assert NewsletterProcessor._normalize_extracted_text("hello   world") == "hello world"

    def test_tightens_punctuation(self):
        assert NewsletterProcessor._normalize_extracted_text("hello , world .") == "hello, world."

    def test_tightens_opening_brackets(self):
        assert NewsletterProcessor._normalize_extracted_text("( hello )") == "(hello)"

    def test_tightens_square_brackets(self):
        assert NewsletterProcessor._normalize_extracted_text("[ item ]") == "[item]"

    def test_tightens_curly_braces(self):
        assert NewsletterProcessor._normalize_extracted_text("{ key }") == "{key}"

    def test_empty_string(self):
        assert NewsletterProcessor._normalize_extracted_text("") == ""

    def test_newlines_and_tabs(self):
        assert NewsletterProcessor._normalize_extracted_text("hello\n\tworld") == "hello world"

    def test_combined_normalization(self):
        result = NewsletterProcessor._normalize_extracted_text("AI  ( research )  , papers .")
        assert result == "AI (research), papers."


# ────────────────────────────────────────────
# _classify_root_section (staticmethod)
# ────────────────────────────────────────────

class TestClassifyRootSection:
    def test_twitter(self):
        assert NewsletterProcessor._classify_root_section("AI Twitter Recap") == "twitter"

    def test_reddit(self):
        assert NewsletterProcessor._classify_root_section("AI Reddit Recap") == "reddit"

    def test_discord_recap(self):
        assert NewsletterProcessor._classify_root_section("AI Discord Recap") == "discord_recap"

    def test_discord_high_level(self):
        assert NewsletterProcessor._classify_root_section("Discord: High Level Summaries") == "discord_high_level"

    def test_discord_detailed(self):
        assert NewsletterProcessor._classify_root_section("Discord: Detailed Channel Summaries") == "discord_detailed"

    def test_other(self):
        assert NewsletterProcessor._classify_root_section("Some Other Section") == "other"

    def test_case_insensitivity(self):
        assert NewsletterProcessor._classify_root_section("ai twitter recap") == "twitter"
        assert NewsletterProcessor._classify_root_section("AI REDDIT RECAP") == "reddit"
        assert NewsletterProcessor._classify_root_section("discord: high level") == "discord_high_level"


# ────────────────────────────────────────────
# _group_segments (instance method)
# ────────────────────────────────────────────

class TestGroupSegments:
    def test_basic_grouping(self, processor):
        segments = [
            {"segment_type": "topic_header", "content_raw": "Topic A"},
            {"segment_type": "item", "content_raw": "Item 1"},
            {"segment_type": "item", "content_raw": "Item 2"},
            {"segment_type": "topic_header", "content_raw": "Topic B"},
            {"segment_type": "item", "content_raw": "Item 3"},
        ]
        groups = processor._group_segments(segments)
        assert len(groups) == 2
        assert groups[0]["label"] == "Topic A"
        assert len(groups[0]["segments"]) == 2
        assert groups[1]["label"] == "Topic B"
        assert len(groups[1]["segments"]) == 1

    def test_loose_items_get_general_group(self, processor):
        segments = [
            {"segment_type": "item", "content_raw": "Orphan item"},
        ]
        groups = processor._group_segments(segments)
        assert len(groups) == 1
        assert groups[0]["label"] == "General"
        assert len(groups[0]["segments"]) == 1

    def test_empty_groups_filtered(self, processor):
        segments = [
            {"segment_type": "topic_header", "content_raw": "Empty Topic"},
            {"segment_type": "topic_header", "content_raw": "Has Items"},
            {"segment_type": "item", "content_raw": "Item 1"},
        ]
        groups = processor._group_segments(segments)
        assert len(groups) == 1
        assert groups[0]["label"] == "Has Items"

    def test_section_headers_kept_even_if_empty(self, processor):
        segments = [
            {"segment_type": "section_header", "content_raw": "Section Nav"},
            {"segment_type": "topic_header", "content_raw": "Topic A"},
            {"segment_type": "item", "content_raw": "Item 1"},
        ]
        groups = processor._group_segments(segments)
        assert len(groups) == 2
        assert groups[0]["label"] == "Section Nav"
        assert groups[0].get("is_section_header") is True
        assert groups[1]["label"] == "Topic A"

    def test_reindexing_after_filter(self, processor):
        segments = [
            {"segment_type": "topic_header", "content_raw": "Empty"},
            {"segment_type": "topic_header", "content_raw": "Has Item"},
            {"segment_type": "item", "content_raw": "Item"},
        ]
        groups = processor._group_segments(segments)
        assert groups[0]["order_index"] == 0

    def test_empty_input(self, processor):
        groups = processor._group_segments([])
        assert groups == []


# ────────────────────────────────────────────
# _extract_entry_data (staticmethod)
# ────────────────────────────────────────────

class FakeEntry(dict):
    """Mimics feedparser's dict+attribute hybrid access pattern."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class TestExtractEntryData:
    def test_basic_extraction(self):
        entry = FakeEntry(
            link="https://example.com/issue-1",
            title="Issue 1",
            published="Mon, 01 Jan 2024 00:00:00 GMT",
            content=[FakeEntry(value="<p>Hello</p>")],
        )
        result = NewsletterProcessor._extract_entry_data(entry)
        assert result is not None
        url, title, html, published = result
        assert url == "https://example.com/issue-1"
        assert title == "Issue 1"
        assert html == "<p>Hello</p>"
        assert published is not None
        assert "2024-01-01" in published

    def test_missing_link_returns_none(self):
        entry = FakeEntry(
            title="No Link",
            content=[FakeEntry(value="<p>Content</p>")],
        )
        result = NewsletterProcessor._extract_entry_data(entry)
        assert result is None

    def test_missing_content_returns_none(self):
        entry = FakeEntry(
            link="https://example.com",
            title="No Content",
        )
        result = NewsletterProcessor._extract_entry_data(entry)
        assert result is None

    def test_summary_fallback(self):
        entry = FakeEntry(
            link="https://example.com",
            title="Summary Only",
            summary="<p>Summary text</p>",
        )
        result = NewsletterProcessor._extract_entry_data(entry)
        assert result is not None
        _, _, html, _ = result
        assert html == "<p>Summary text</p>"

    def test_bad_date_gives_none_published(self):
        entry = FakeEntry(
            link="https://example.com",
            title="Bad Date",
            published="not-a-date",
            content=[FakeEntry(value="<p>Content</p>")],
        )
        result = NewsletterProcessor._extract_entry_data(entry)
        assert result is not None
        _, _, _, published = result
        assert published is None


# ────────────────────────────────────────────
# check_issue_exists
# ────────────────────────────────────────────

class TestCheckIssueExists:
    def _make_supabase_mock(self, processor, url_rows=None, title_rows=None):
        """Wire processor.supabase so URL query returns url_rows and title query returns title_rows."""
        from unittest.mock import MagicMock

        url_result = MagicMock()
        url_result.data = url_rows or []

        title_result = MagicMock()
        title_result.data = title_rows or []

        call_count = [0]

        def select_side_effect(*args, **kwargs):
            q = MagicMock()
            # First .eq("url", ...) call → URL lookup; second chain → source+title lookup
            eq_call_count = [0]

            def eq_side_effect(col, val):
                eq_call_count[0] += 1
                inner_q = MagicMock()
                inner_q.execute.return_value = url_result if col == "url" else title_result
                # Support chaining: .eq("source", ...).eq("title", ...)
                inner_q.eq.side_effect = lambda c, v: MagicMock(execute=MagicMock(return_value=title_result))
                return inner_q

            q.eq.side_effect = eq_side_effect
            return q

        processor.supabase.table.return_value.select.side_effect = select_side_effect

    def test_url_match_returns_true(self, processor):
        self._make_supabase_mock(processor, url_rows=[{"id": "abc"}])
        assert processor.check_issue_exists("https://example.com/issue-1") is True

    def test_no_match_returns_false(self, processor):
        self._make_supabase_mock(processor, url_rows=[], title_rows=[])
        assert processor.check_issue_exists("https://example.com/new", title="New Issue", source="ainews") is False

    def test_source_title_match_catches_renamed_slug(self, processor):
        """Renamed slug: URL is new but source+title already exist → should return True."""
        from unittest.mock import MagicMock

        url_result = MagicMock()
        url_result.data = []  # URL not found

        title_result = MagicMock()
        title_result.data = [{"id": "abc", "url": "https://example.com/old-slug"}]  # title found

        table_mock = MagicMock()
        # First call: URL lookup (returns empty)
        # Second call: source+title lookup (returns a match)
        table_mock.select.return_value.eq.return_value.execute.return_value = url_result
        table_mock.select.return_value.eq.return_value.eq.return_value.execute.return_value = title_result

        processor.supabase.table.return_value = table_mock

        assert processor.check_issue_exists(
            "https://example.com/new-slug",
            title="Same Title",
            source="ainews",
        ) is True

    def test_skips_title_check_when_no_title(self, processor):
        """Without title/source, only URL check runs — no crash."""
        from unittest.mock import MagicMock

        url_result = MagicMock()
        url_result.data = []
        processor.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = url_result

        assert processor.check_issue_exists("https://example.com/issue") is False

    def test_supabase_error_returns_false(self, processor):
        """DB error should return False (allow processing attempt)."""
        processor.supabase.table.side_effect = Exception("DB down")
        assert processor.check_issue_exists("https://example.com/issue", title="T", source="ainews") is False
