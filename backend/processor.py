"""
Newsletter processor: RSS fetch, parse, clean, TTS, and storage.
"""
import logging
import asyncio
import io
from typing import List, Dict, Optional
from datetime import datetime, timezone
import json
import uuid

import httpx
import feedparser
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

from google.cloud import texttospeech
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel

from supabase import create_client, Client


class NewsletterProcessor:
    """Processes newsletters: fetch, parse, clean, TTS, and store."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        gcp_project_id: str,
        gcp_region: str,
        gcs_bucket_name: str,
        gemini_model_name: str = "gemini-3-pro-preview",
        max_concurrent_segments: int = 5,
        tts_voice_name: str = "en-US-Chirp3-HD-Aoede",
    ):
        """Initialize processor with credentials."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.gcp_project_id = gcp_project_id
        self.gcp_region = gcp_region
        self.gcs_bucket_name = gcs_bucket_name
        self.max_concurrent_segments = max_concurrent_segments

        # Initialize GCP clients
        # Gemini 3 Pro Preview requires global region
        vertexai.init(project=gcp_project_id, location="global")
        self.gemini_model = GenerativeModel(gemini_model_name)
        logger.info(f"Initialized processor with Gemini model: {gemini_model_name}")
        self.tts_client = texttospeech.TextToSpeechClient()
        self.storage_client = storage.Client()

        # TTS voice configuration
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=tts_voice_name,
        )
        logger.info(f"Using TTS voice: {tts_voice_name}")
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
        )
        
        # Shared HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close resources."""
        await self.http_client.aclose()

    async def process_newsletter(self, url: str, issue_id: Optional[str] = None) -> str:
        """
        Main processing pipeline for a newsletter issue.

        Args:
            url: URL of the newsletter issue
            issue_id: Optional pre-generated issue UUID (for background tasks)

        Returns:
            str: Issue UUID
        """
        logger.info(f"Processing newsletter: {url}")

        # Fetch and parse RSS/HTML
        raw_content = await self._fetch_newsletter(url)
        issue_data, segments_data = await asyncio.to_thread(self._parse_newsletter, raw_content, url)
        logger.info(f"Parsed {len(segments_data)} segments from newsletter")

        # Use provided issue_id or get from upsert
        if issue_id:
            # For background tasks, insert with specific ID
            issue_data["id"] = issue_id
            self.supabase.table("issues").upsert(
                issue_data,
                on_conflict="url"
            ).execute()
        else:
            # Upsert issue to handle race conditions
            issue_result = self.supabase.table("issues").upsert(
                issue_data,
                on_conflict="url"
            ).execute()
            issue_id = issue_result.data[0]["id"]

        # Delete old segments if reprocessing
        self.supabase.table("segments").delete().eq("issue_id", issue_id).execute()

        # Process segments in parallel with rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent_segments)

        async def process_segment(segment: Dict) -> Dict:
            async with semaphore:
                segment["issue_id"] = issue_id
                # Clean text with Gemini
                clean_text = await self._clean_text_for_tts(segment["content_raw"])
                segment["content_clean"] = clean_text
                # Generate audio with TTS
                audio_url, duration_ms = await self._generate_audio(
                    clean_text, issue_id, segment["order_index"]
                )
                segment["audio_url"] = audio_url
                segment["audio_duration_ms"] = duration_ms
                logger.debug(f"Processed segment {segment['order_index']}")
                return segment

        # Process all segments concurrently
        segments_results = await asyncio.gather(
            *[process_segment(s) for s in segments_data],
            return_exceptions=True
        )

        # Filter out exceptions and log them
        segments_data = []
        for i, result in enumerate(segments_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process segment {i}: {result}")
            else:
                segments_data.append(result)

        # Store all successfully processed segments
        if segments_data:
            self.supabase.table("segments").insert(segments_data).execute()
            logger.info(f"Stored {len(segments_data)} segments for issue {issue_id}")
        else:
            logger.warning(f"No segments were successfully processed for issue {issue_id}")

        # Mark issue as processed
        self.supabase.table("issues").update(
            {"processed_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", issue_id).execute()

        logger.info(f"Newsletter processing complete: {issue_id}")
        return issue_id

    async def _fetch_newsletter(self, url: str) -> str:
        """Fetch newsletter content from URL."""
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_newsletter(self, html_content: str, url: str) -> tuple[Dict, List[Dict]]:
        """
        Parse AINews newsletter HTML into structured segments.

        Args:
            html_content: Raw HTML
            url: Newsletter URL

        Returns:
            tuple: (issue_data, segments_data)
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract issue metadata
        title = soup.find("title").text if soup.find("title") else "Untitled"
        published_at = datetime.now(timezone.utc).isoformat()

        issue_data = {
            "title": title,
            "url": url,
            "published_at": published_at,
        }

        # Find main article content
        article = soup.find("article") or soup.find("div", class_=lambda x: x and "content" in x)

        if not article:
            # Fallback to body if no article found
            article = soup.find("body")

        segments_data = []
        order_index = 0

        # Parse AINews structure: h1/h2/h3 headers followed by list items
        for element in article.find_all(["h1", "h2", "h3", "li"]):
            if element.name in ["h1", "h2", "h3"]:
                # Section header
                text = element.get_text(strip=True)
                if text:  # Only add non-empty headers
                    segments_data.append({
                        "segment_type": "section_header",
                        "content_raw": text,
                        "links": [],
                        "order_index": order_index,
                    })
                    order_index += 1

            elif element.name == "li":
                # News item
                text = element.get_text(strip=True)
                if text and len(text) > 20:  # Filter out very short items
                    # Extract links
                    links = [
                        {"text": a.get_text(strip=True), "url": a.get("href")}
                        for a in element.find_all("a")
                        if a.get("href")  # Only include links with href
                    ]

                    segments_data.append({
                        "segment_type": "item",
                        "content_raw": text,
                        "links": links,
                        "order_index": order_index,
                    })
                    order_index += 1

        return issue_data, segments_data

    async def _clean_text_for_tts(self, raw_text: str) -> str:
        """
        Clean text for natural TTS using Gemini.

        Args:
            raw_text: Original text with links, mentions, etc.

        Returns:
            str: Cleaned text for TTS
        """
        prompt = """
Clean the following newsletter text for text-to-speech. Apply these rules:

1. Replace "@username" with "[username] tweeted"
2. Replace "/r/subreddit" with "the [subreddit] subreddit"
3. For markdown links [text](url), keep only the text, remove the URL
4. If this is a section header, prefix with "Now:"
5. Remove any other formatting that sounds unnatural when read aloud
6. Keep the text conversational and natural

<text_to_clean>
{raw_text}
</text_to_clean>

Return ONLY the cleaned text, no explanations.
""".format(raw_text=raw_text)

        response = await asyncio.to_thread(
            self.gemini_model.generate_content,
            prompt
        )
        return response.text.strip()

    async def _generate_audio(
        self, text: str, issue_id: str, segment_index: int
    ) -> tuple[str, int]:
        """
        Generate audio using Google Cloud TTS.

        Args:
            text: Cleaned text to synthesize
            issue_id: Issue UUID
            segment_index: Segment order index

        Returns:
            tuple: (gcs_url, duration_ms)
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Generate audio
        response = await asyncio.to_thread(
            self.tts_client.synthesize_speech,
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config,
        )

        # Upload to GCS
        blob_name = f"{issue_id}/segment_{segment_index}.mp3"
        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blob = bucket.blob(blob_name)

        await asyncio.to_thread(
            blob.upload_from_string,
            response.audio_content,
            content_type="audio/mpeg",
        )

        # Make blob public or generate signed URL
        blob.make_public()
        audio_url = blob.public_url

        # Extract actual duration from MP3 metadata
        audio_file = io.BytesIO(response.audio_content)
        audio = MP3(audio_file)
        duration_ms = int(audio.info.length * 1000)

        return audio_url, duration_ms

    async def get_issue_status(self, issue_id: str) -> Optional[Dict]:
        """
        Get processing status for an issue.

        Args:
            issue_id: Issue UUID

        Returns:
            dict: Issue status and segment count
        """
        result = self.supabase.table("issues").select("*").eq("id", issue_id).execute()

        if not result.data:
            return None

        issue = result.data[0]

        # Get segment count
        segments = (
            self.supabase.table("segments")
            .select("id", count="exact")
            .eq("issue_id", issue_id)
            .execute()
        )

        return {
            "issue": issue,
            "segment_count": len(segments.data) if segments.data else 0,
            "status": "completed" if issue.get("processed_at") else "processing",
        }

    async def fetch_latest_newsletter_url(self) -> Optional[str]:
        """
        Fetch the latest newsletter URL from the AINews RSS feed.
        
        This method is used by Cloud Scheduler to discover new issues
        without hardcoding URLs in the scheduler configuration.

        Returns:
            str: URL of the latest newsletter issue, or None if fetch fails
        """
        rss_url = "https://buttondown.com/ainews/rss"
        logger.info(f"Fetching RSS feed: {rss_url}")
        
        try:
            response = await self.http_client.get(rss_url)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = await asyncio.to_thread(feedparser.parse, response.text)
            
            if not feed.entries:
                logger.warning("No entries found in RSS feed")
                return None
            
            # Get the most recent entry's link
            latest_entry = feed.entries[0]
            latest_url = latest_entry.get("link")
            
            if latest_url:
                logger.info(f"Found latest newsletter URL: {latest_url}")
                return latest_url
            else:
                logger.warning("Latest RSS entry has no link")
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch RSS feed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return None

    def check_issue_exists(self, url: str) -> bool:
        """
        Check if an issue with the given URL already exists in the database.
        
        Used to prevent duplicate processing when Cloud Scheduler triggers
        and the newsletter hasn't been updated yet.

        Args:
            url: Newsletter URL to check

        Returns:
            bool: True if issue already exists, False otherwise
        """
        try:
            result = self.supabase.table("issues").select("id").eq("url", url).execute()
            exists = len(result.data) > 0
            if exists:
                logger.info(f"Issue already exists for URL: {url}")
            return exists
        except Exception as e:
            logger.error(f"Error checking issue existence: {e}")
            # Return False to allow processing attempt (will be caught by upsert)
            return False
