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

class TestParseNewsletterDedup:
    """Regression tests: duplicate headers in source HTML should be deduplicated."""

    def test_duplicate_section_headers_deduped(self, processor):
        """If the HTML contains the same h1 section header multiple times,
        only one section_header segment should be emitted per unique heading."""
        html = """
        <article>
            <h1>Everyone launching everything everywhere all at once.</h1>
            <p>Some intro paragraph with enough text to pass the length filter.</p>
            <h1>AI Twitter Recap</h1>
            <p>Some twitter content that is long enough to be included.</p>
            <h1>AI Twitter Recap</h1>
            <p>Duplicate twitter section content that is also long enough.</p>
            <h1>AI Twitter Recap</h1>
            <p>Third duplicate twitter section that repeats the header again.</p>
        </article>
        """
        _, segments = processor._parse_newsletter(html, "https://example.com/test")
        section_headers = [s for s in segments if s["segment_type"] == "section_header"]
        section_labels = [s["content_raw"] for s in section_headers]
        # "AI Twitter Recap" should appear only once as a section header
        assert section_labels.count("AI Twitter Recap") == 1

    def test_duplicate_topic_headers_deduped(self, processor):
        """If the HTML contains the same topic header multiple times,
        only one topic_header segment should be emitted per unique heading."""
        html = """
        <article>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Content about Qwen 3.5 that is long enough to pass filter.</p>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Duplicate content about Qwen that is also long enough here.</p>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Triple duplicate Qwen content with sufficient length to pass.</p>
        </article>
        """
        _, segments = processor._parse_newsletter(html, "https://example.com/test")
        topic_headers = [s for s in segments if s["segment_type"] == "topic_header"]
        topic_labels = [s["content_raw"] for s in topic_headers]
        # Same topic header should appear only once
        assert topic_labels.count("Frontier model ecosystem: Qwen 3.5") == 1

    def test_groups_not_duplicated_after_dedup(self, processor):
        """End-to-end: parse + group should not produce duplicate TOC entries."""
        html = """
        <article>
            <h1>Everyone launching everything everywhere all at once.</h1>
            <p>Intro paragraph with enough content to pass the length filter.</p>
            <h1>AI Twitter Recap</h1>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Content about Qwen that is long enough to be included as an item.</p>
            <h1>AI Twitter Recap</h1>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Duplicate content about Qwen that is also long enough to include.</p>
            <h1>AI Twitter Recap</h1>
            <h2>Frontier model ecosystem: Qwen 3.5</h2>
            <p>Third duplicate content about Qwen sufficient to pass filter here.</p>
        </article>
        """
        _, segments = processor._parse_newsletter(html, "https://example.com/test")
        groups = processor._group_segments(segments)
        group_labels = [g["label"] for g in groups]
        assert group_labels.count("AI Twitter Recap") == 1
        assert group_labels.count("Frontier model ecosystem: Qwen 3.5") == 1


class TestParseNewsletterContainerDetection:
    """Regression: content container class matching must be exact, not substring."""

    def test_footnote_content_not_matched_as_content(self, processor):
        """A div with class 'footnote-content' must NOT be selected as the
        content container when looking for class 'content'.  The parser should
        fall through and find all <p> tags in the document instead."""
        html = """
        <p>First real paragraph with enough text to pass the length filter easily.</p>
        <p>Second real paragraph also long enough to pass the minimum length check.</p>
        <div class="footnote-content">
            <p>Tiny footnote text that is just a citation reference in the article.</p>
        </div>
        <p>Third real paragraph providing more content for the article overall.</p>
        """
        _, segments = processor._parse_newsletter(html, "https://example.com/test")
        items = [s for s in segments if s["segment_type"] == "item"]
        # Should find 3 real paragraphs + 1 footnote paragraph = 4 items
        # (not just the 1 footnote paragraph from the old substring match)
        assert len(items) >= 3


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
    def _mock_url_only(self, processor, url_rows):
        """Mock supabase so URL lookup returns url_rows."""
        from unittest.mock import MagicMock

        url_result = MagicMock()
        url_result.data = url_rows
        processor.supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = url_result

    def _mock_url_and_slug_rename(self, processor, url_rows, slug_rename_rows):
        """Mock supabase for URL lookup (empty) + source+title+date lookup."""
        from unittest.mock import MagicMock

        url_result = MagicMock()
        url_result.data = url_rows

        slug_result = MagicMock()
        slug_result.data = slug_rename_rows

        table_mock = MagicMock()
        # URL lookup: .select().eq("url", ...).execute()
        table_mock.select.return_value.eq.return_value.execute.return_value = url_result
        # Slug-rename lookup: .select().eq("source").eq("title").gte().lte().execute()
        table_mock.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = slug_result

        processor.supabase.table.return_value = table_mock

    def test_url_match_returns_true(self, processor):
        self._mock_url_only(processor, url_rows=[{"id": "abc"}])
        assert processor.check_issue_exists("https://example.com/issue-1") is True

    def test_no_match_returns_false(self, processor):
        self._mock_url_and_slug_rename(processor, url_rows=[], slug_rename_rows=[])
        assert processor.check_issue_exists(
            "https://example.com/new", title="New Issue", source="ainews",
            published_at="2026-03-03T05:44:39+00:00",
        ) is False

    def test_source_title_date_match_catches_renamed_slug(self, processor):
        """Renamed slug: URL is new but source+title+date already exist → True."""
        self._mock_url_and_slug_rename(
            processor, url_rows=[],
            slug_rename_rows=[{"id": "abc", "url": "https://example.com/old-slug"}],
        )
        assert processor.check_issue_exists(
            "https://example.com/new-slug",
            title="Same Title",
            source="ainews",
            published_at="2026-02-25T05:44:39+00:00",
        ) is True

    def test_same_title_different_date_not_duplicate(self, processor):
        """Regression: recurring titles like 'not much happened today' on different
        dates must NOT be treated as duplicates."""
        self._mock_url_and_slug_rename(processor, url_rows=[], slug_rename_rows=[])
        # March 3 issue should NOT match the Feb 20 issue with the same title
        assert processor.check_issue_exists(
            "https://news.smol.ai/issues/26-03-03-not-much/",
            title="not much happened today",
            source="ainews",
            published_at="2026-03-03T05:44:39+00:00",
        ) is False

    def test_skips_slug_rename_check_without_published_at(self, processor):
        """Without published_at, only URL check runs — no false positives."""
        self._mock_url_only(processor, url_rows=[])
        assert processor.check_issue_exists(
            "https://example.com/issue", title="T", source="ainews",
        ) is False

    def test_skips_title_check_when_no_title(self, processor):
        """Without title/source, only URL check runs — no crash."""
        self._mock_url_only(processor, url_rows=[])
        assert processor.check_issue_exists("https://example.com/issue") is False

    def test_supabase_error_returns_false(self, processor):
        """DB error should return False (allow processing attempt)."""
        processor.supabase.table.side_effect = Exception("DB down")
        assert processor.check_issue_exists("https://example.com/issue", title="T", source="ainews") is False
