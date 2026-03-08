"""Tests for multi-source newsletter support."""
import os
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import Config
from processor import NewsletterProcessor


# ────────────────────────────────────────────
# Config tests
# ────────────────────────────────────────────

class TestConfig:
    def test_newsletter_sources_loaded(self):
        expected = [
            "ainews", "the_batch", "tongyi_weekly",
            "import_ai", "last_week_in_ai", "the_sequence",
            "interconnects", "ahead_of_ai", "normal_tech", "latent_space",
        ]
        for src_id in expected:
            assert src_id in Config.NEWSLETTER_SOURCES, f"{src_id} not found in NEWSLETTER_SOURCES"
        assert len(Config.NEWSLETTER_SOURCES) == 10

    def test_default_source(self):
        assert Config.DEFAULT_SOURCE_ID == "ainews"

    def test_get_source_config_valid(self):
        cfg = Config.get_source_config("ainews")
        assert "latent.space/feed" in cfg["rssUrl"]
        assert "sectionId=327741" in cfg["rssUrl"]

    def test_get_source_config_the_batch(self):
        cfg = Config.get_source_config("the_batch")
        assert cfg["filterBundleOnly"] is True
        assert "charonhub.deeplearning.ai" in cfg["rssUrl"]

    def test_get_source_config_tongyi(self):
        cfg = Config.get_source_config("tongyi_weekly")
        assert "tongyilab.substack.com" in cfg["rssUrl"]

    def test_get_source_config_import_ai(self):
        cfg = Config.get_source_config("import_ai")
        assert "jack-clark.net" in cfg["rssUrl"]

    def test_get_source_config_last_week_in_ai(self):
        cfg = Config.get_source_config("last_week_in_ai")
        assert "lastweekin.ai" in cfg["rssUrl"]
        assert cfg["titleFilter"] == "^Last Week in AI"

    def test_get_source_config_the_sequence(self):
        cfg = Config.get_source_config("the_sequence")
        assert "thesequence.substack.com" in cfg["rssUrl"]

    def test_get_source_config_interconnects(self):
        cfg = Config.get_source_config("interconnects")
        assert "interconnects.ai" in cfg["rssUrl"]

    def test_get_source_config_ahead_of_ai(self):
        cfg = Config.get_source_config("ahead_of_ai")
        assert "sebastianraschka.com" in cfg["rssUrl"]

    def test_get_source_config_normal_tech(self):
        cfg = Config.get_source_config("normal_tech")
        assert "normaltech.ai" in cfg["rssUrl"]

    def test_get_source_config_latent_space(self):
        cfg = Config.get_source_config("latent_space")
        assert "latent.space" in cfg["rssUrl"]
        assert cfg["titleFilter"] == "^(?!\\[AINews\\])"

    def test_get_source_config_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            Config.get_source_config("nonexistent")

    def test_source_configs_have_required_fields(self):
        for src_id, cfg in Config.NEWSLETTER_SOURCES.items():
            assert "id" in cfg, f"{src_id} missing 'id'"
            assert "name" in cfg, f"{src_id} missing 'name'"
            assert "rssUrl" in cfg, f"{src_id} missing 'rssUrl'"


# ────────────────────────────────────────────
# Title filter tests
# ────────────────────────────────────────────

class TestTitleFilter:
    """Verify titleFilter regex patterns work correctly."""

    def test_last_week_in_ai_matches_newsletter(self):
        pattern = Config.get_source_config("last_week_in_ai")["titleFilter"]
        assert re.search(pattern, "Last Week in AI #335")

    def test_last_week_in_ai_skips_podcast(self):
        pattern = Config.get_source_config("last_week_in_ai")["titleFilter"]
        assert not re.search(pattern, "LWiAI Podcast #234")

    def test_latent_space_matches_essay(self):
        pattern = Config.get_source_config("latent_space")["titleFilter"]
        assert re.search(pattern, "Bitter Lessons in Venture")

    def test_latent_space_matches_interview(self):
        pattern = Config.get_source_config("latent_space")["titleFilter"]
        assert re.search(pattern, "Building AI Agents with LangChain")

    def test_latent_space_skips_ainews(self):
        pattern = Config.get_source_config("latent_space")["titleFilter"]
        assert not re.search(pattern, "[AINews] The Custom ASIC Thesis")

    @pytest.mark.asyncio
    async def test_fetch_title_filtered_skips_non_matching(self, processor):
        """Integration: fetch_latest_newsletter with titleFilter skips non-matching entries."""
        mock_entry_podcast = MagicMock()
        mock_entry_podcast.get = lambda k, d="": {
            "title": "LWiAI Podcast #234",
            "link": "https://lastweekin.ai/p/podcast-234",
        }.get(k, d)

        mock_entry_newsletter = MagicMock()
        mock_entry_newsletter.get = lambda k, d="": {
            "title": "Last Week in AI #335",
            "link": "https://lastweekin.ai/p/last-week-335",
        }.get(k, d)
        mock_entry_newsletter.content = [{"value": "<p>Newsletter content here</p>"}]
        mock_entry_newsletter.get = lambda k, d="": {
            "title": "Last Week in AI #335",
            "link": "https://lastweekin.ai/p/last-week-335",
            "published": "Mon, 01 Jan 2024 00:00:00 GMT",
            "content": mock_entry_newsletter.content,
            "summary": "<p>Newsletter content here</p>",
        }.get(k, d)

        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry_podcast, mock_entry_newsletter]

        mock_response = MagicMock()
        mock_response.text = "<rss>fake</rss>"
        mock_response.raise_for_status = MagicMock()

        proc = processor
        proc.http_client = AsyncMock()
        proc.http_client.get = AsyncMock(return_value=mock_response)

        with patch("processor.feedparser.parse", return_value=mock_feed):
            result = await proc.fetch_latest_newsletter(entry_index=0, source_id="last_week_in_ai")

        assert result is not None
        url, title, _, _, source = result
        assert "last-week-335" in url
        assert title == "Last Week in AI #335"
        assert source == "last_week_in_ai"


# ────────────────────────────────────────────
# Bundle filter tests
# ────────────────────────────────────────────

class TestBundleFilter:
    def test_bundle_url_with_issue_id(self):
        assert NewsletterProcessor._is_bundle_entry(
            "https://charonhub.deeplearning.ai/issue-341/"
        ) is True

    def test_bundle_url_with_issue_id_no_trailing_slash(self):
        assert NewsletterProcessor._is_bundle_entry(
            "https://charonhub.deeplearning.ai/issue-340"
        ) is True

    def test_individual_article_slug_url(self):
        assert NewsletterProcessor._is_bundle_entry(
            "https://charonhub.deeplearning.ai/why-hollywood-worries-about-ai/"
        ) is False

    def test_individual_article_with_commas_in_title_but_slug_url(self):
        """Articles with commas in title but slug URL should NOT be bundles."""
        assert NewsletterProcessor._is_bundle_entry(
            "https://charonhub.deeplearning.ai/meta-amazon-microsoft-google-and-nvidia-pour-millions-into-government-influence/"
        ) is False

    def test_empty_url(self):
        assert NewsletterProcessor._is_bundle_entry("") is False


# ────────────────────────────────────────────
# Parse newsletter consolidation guards
# ────────────────────────────────────────────

class TestParseConsolidationGuards:
    """Verify that Discord/Reddit consolidation only applies to ainews source."""

    def test_ainews_discord_consolidation_active(self, processor):
        """Discord consolidation should filter discord_detailed for ainews."""
        proc = processor
        html = """
        <article>
            <h1>AI Discord Recap</h1>
            <p>Some recap content that is long enough to pass the filter</p>
            <h1>Discord: Detailed Channel Summaries</h1>
            <p>This detailed content should be skipped for ainews source</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="ainews")
        # With recap_only mode, discord_detailed content should be filtered out
        texts = [s["content_raw"] for s in segments]
        assert not any("detailed content should be skipped" in t.lower() for t in texts)

    def test_the_batch_discord_consolidation_inactive(self, processor):
        """Discord consolidation should NOT filter for non-ainews sources."""
        proc = processor
        html = """
        <article>
            <h1>AI Discord Recap</h1>
            <p>Some recap content that is long enough to pass the filter</p>
            <h1>Discord: Detailed Channel Summaries</h1>
            <p>This detailed content should be kept for non-ainews source</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="the_batch")
        texts = [s["content_raw"] for s in segments]
        assert any("detailed content should be kept" in t.lower() for t in texts)

    def test_null_source_defaults_to_ainews_behavior(self, processor):
        """source_id=None should behave like ainews (consolidation active)."""
        proc = processor
        html = """
        <article>
            <h1>AI Discord Recap</h1>
            <p>Some recap content that is long enough to pass the filter</p>
            <h1>Discord: Detailed Channel Summaries</h1>
            <p>This detailed content should be skipped when source is None</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id=None)
        texts = [s["content_raw"] for s in segments]
        assert not any("detailed content should be skipped" in t.lower() for t in texts)


# ────────────────────────────────────────────
# Source-specific content filtering
# ────────────────────────────────────────────

class TestSourceContentFiltering:
    """Verify source-specific junk text is filtered out."""

    def test_elevenlabs_loader_text_filtered(self, processor):
        """The Batch's ElevenLabs TTS loader text should be stripped."""
        proc = processor
        html = """
        <article>
            <p>Loading the Elevenlabs Text to Speech AudioNative Player...</p>
            <h2>Dear friends,</h2>
            <p>This is actual newsletter content that should be kept here.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="the_batch")
        texts = [s["content_raw"] for s in segments]
        assert not any("elevenlabs" in t.lower() for t in texts)
        assert any("actual newsletter content" in t.lower() for t in texts)

    def test_want_more_stay_updated_and_trailing_removed(self, processor):
        """Tongyi's 'Want More? Stay Updated' and everything after should be stripped."""
        proc = processor
        html = """
        <article>
            <h2>Real Content Topic</h2>
            <p>This is a real article paragraph with enough text to keep.</p>
            <h3>Want More? Stay Updated.</h3>
            <p>Every week, we bring you new model releases and upgrades.</p>
            <p>Subscribe to The Tongyi Weekly and never miss a release.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="tongyi_weekly")
        texts = [s["content_raw"] for s in segments]
        assert any("real article paragraph" in t.lower() for t in texts)
        assert not any("every week" in t.lower() for t in texts)
        assert not any("subscribe" in t.lower() for t in texts)

    def test_want_more_with_emoji_filtered(self, processor):
        """The emoji variant should also be caught."""
        proc = processor
        html = """
        <article>
            <p>Good content that passes the length filter easily here.</p>
            <h3>\U0001f4ec Want More? Stay Updated.</h3>
            <p>Promotional trailing text that should be removed entirely.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test")
        texts = [s["content_raw"] for s in segments]
        assert not any("promotional" in t.lower() for t in texts)

    def test_filtering_does_not_affect_ainews(self, processor):
        """AINews content with similar-ish text should not be affected."""
        proc = processor
        html = """
        <article>
            <p>Loading a model from HuggingFace is straightforward and easy.</p>
            <p>Want more details? Stay updated on the latest AI research papers.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="ainews")
        texts = [s["content_raw"] for s in segments]
        # "Loading a model" should stay (doesn't match "Loading the Elevenlabs...")
        assert any("loading a model" in t.lower() for t in texts)


# ────────────────────────────────────────────
# API endpoint tests
# ────────────────────────────────────────────

class TestProcessLatestEndpoint:
    """Test the /process-latest endpoint source parameter handling."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        # Need to patch before import to avoid real GCP init
        with patch("processor.create_client"), \
             patch("processor.vertexai"), \
             patch("processor.GenerativeModel"), \
             patch("processor.texttospeech.TextToSpeechClient"), \
             patch("processor.storage.Client"), \
             patch.dict(os.environ, {
                 "SUPABASE_URL": "http://fake",
                 "SUPABASE_SERVICE_KEY": "fake",
                 "GCP_PROJECT_ID": "fake",
                 "GCS_BUCKET_NAME": "fake",
             }):
            # Reimport to pick up patched env
            import importlib
            import main as main_mod
            importlib.reload(main_mod)
            yield TestClient(main_mod.app)

    def test_invalid_source_returns_400(self, client):
        resp = client.post("/process-latest?source=nonexistent")
        assert resp.status_code == 400
        assert "Unknown source" in resp.json()["detail"]

    def test_valid_source_accepted(self, client):
        """Valid source should not 400 (will fail later in processing, but passes validation)."""
        with patch.object(
            NewsletterProcessor, "fetch_latest_newsletter",
            new_callable=AsyncMock, return_value=None
        ):
            resp = client.post("/process-latest?source=the_batch")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "no_new_issue"
            assert body["source"] == "the_batch"

    def test_default_source_when_omitted(self, client):
        """Omitting source should default to ainews."""
        with patch.object(
            NewsletterProcessor, "fetch_latest_newsletter",
            new_callable=AsyncMock, return_value=None
        ):
            resp = client.post("/process-latest")
            assert resp.status_code == 200
            body = resp.json()
            assert body["source"] == "ainews"


# ────────────────────────────────────────────
# Import AI *** section divider parsing
# ────────────────────────────────────────────

class TestImportAISectionDividers:
    """Import AI uses <p>***</p> to separate topics and <strong>-led <p> for headers."""

    def test_asterisk_divider_creates_topic_groups(self, processor):
        """Each *** divider should start a new topic group from the next <strong> header."""
        proc = processor
        html = """
        <article>
            <p>Welcome to Import AI, a newsletter about artificial intelligence.</p>
            <p><strong>First topic title:</strong><em>…Subtitle one…</em>Body of the first topic paragraph.</p>
            <p><strong>Sub-heading one:</strong> Detail under first topic.</p>
            <p>***</p>
            <p><strong>Second topic title:</strong><em>…Subtitle two…</em>Body of the second topic paragraph.</p>
            <p><strong>Sub-heading two:</strong> Detail under second topic.</p>
            <p>***</p>
            <p><strong>Tech Tales:</strong></p>
            <p>A short fiction story about AI futures and possibilities.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="import_ai")

        headers = [s["content_raw"] for s in segments if s["segment_type"] == "topic_header"]
        items = [s["content_raw"] for s in segments if s["segment_type"] == "item"]

        # Three topic headers extracted from strong text
        assert "First topic title:" in headers
        assert "Second topic title:" in headers
        assert "Tech Tales:" in headers

        # *** itself should NOT appear in any segment
        all_text = [s["content_raw"] for s in segments]
        assert "***" not in all_text

        # Full paragraph text emitted as items
        assert any("Body of the first topic" in t for t in items)
        assert any("Body of the second topic" in t for t in items)

    def test_groups_have_correct_labels(self, processor):
        """Grouped segments should produce TOC-friendly labels."""
        proc = processor
        html = """
        <article>
            <p><strong>AI policy update:</strong><em>…New regulation…</em>The EU released new guidelines.</p>
            <p>More details about the regulation are discussed below.</p>
            <p>***</p>
            <p><strong>Robot breakthroughs:</strong><em>…Walking robots…</em>A team demonstrated a new robot.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="import_ai")
        groups = proc._group_segments(segments)

        labels = [g["label"] for g in groups]
        assert "AI policy update:" in labels
        assert "Robot breakthroughs:" in labels

        # First group should have items
        ai_group = next(g for g in groups if g["label"] == "AI policy update:")
        assert len(ai_group["segments"]) >= 2  # paragraph body + "More details"

    def test_non_import_ai_ignores_asterisks(self, processor):
        """For non-import_ai sources, *** should not trigger topic splitting."""
        proc = processor
        html = """
        <article>
            <p>Some content that is long enough to pass the filter.</p>
            <p>***</p>
            <p><strong>Bold text:</strong><em>Subtitle</em>Body text for this paragraph.</p>
        </article>
        """
        _, segments = proc._parse_newsletter(html, "http://test", "Test", source_id="the_batch")

        headers = [s for s in segments if s["segment_type"] == "topic_header"]
        # No topic headers should be detected from the strong-led paragraph
        assert len(headers) == 0
