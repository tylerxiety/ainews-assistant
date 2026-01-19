"""
Newsletter processor: RSS fetch, parse, clean, TTS, and storage.
"""
import asyncio
import httpx
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import json
import uuid

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
    ):
        """Initialize processor with credentials."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.gcp_project_id = gcp_project_id
        self.gcp_region = gcp_region
        self.gcs_bucket_name = gcs_bucket_name

        # Initialize GCP clients
        # Gemini 3 Pro Preview requires global region
        vertexai.init(project=gcp_project_id, location="global")
        self.gemini_model = GenerativeModel("gemini-3-pro-preview")
        self.tts_client = texttospeech.TextToSpeechClient()
        self.storage_client = storage.Client()

        # TTS voice configuration
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Chirp3-HD-Aoede",
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
        )

    async def process_newsletter(self, url: str) -> str:
        """
        Main processing pipeline for a newsletter issue.

        Args:
            url: URL of the newsletter issue

        Returns:
            str: Issue UUID
        """
        # Fetch and parse RSS/HTML
        raw_content = await self._fetch_newsletter(url)
        issue_data, segments_data = self._parse_newsletter(raw_content, url)

        # Check if issue already exists
        existing_issue = self.supabase.table("issues").select("*").eq("url", url).execute()

        if existing_issue.data:
            # Issue exists, delete old segments and reprocess
            issue_id = existing_issue.data[0]["id"]
            self.supabase.table("segments").delete().eq("issue_id", issue_id).execute()
        else:
            # Create new issue
            issue_result = self.supabase.table("issues").insert(issue_data).execute()
            issue_id = issue_result.data[0]["id"]

        # Process each segment
        for segment in segments_data:
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

        # Store all segments
        self.supabase.table("segments").insert(segments_data).execute()

        # Mark issue as processed
        self.supabase.table("issues").update(
            {"processed_at": datetime.utcnow().isoformat()}
        ).eq("id", issue_id).execute()

        return issue_id

    async def _fetch_newsletter(self, url: str) -> str:
        """Fetch newsletter content from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
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
        published_at = datetime.utcnow().isoformat()

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
        prompt = f"""
Clean the following newsletter text for text-to-speech. Apply these rules:

1. Replace "@username" with "[username] tweeted"
2. Replace "/r/subreddit" with "the [subreddit] subreddit"
3. For markdown links [text](url), keep only the text, remove the URL
4. If this is a section header, prefix with "Now:"
5. Remove any other formatting that sounds unnatural when read aloud
6. Keep the text conversational and natural

Text to clean:
{raw_text}

Return ONLY the cleaned text, no explanations.
"""

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

        # Calculate duration (approximate from text length)
        # More accurate: use audio file metadata
        duration_ms = len(text) * 60  # ~60ms per character (rough estimate)

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
