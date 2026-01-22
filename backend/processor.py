"""
Newsletter processor: RSS fetch, parse, clean, TTS, and storage.
"""
import asyncio
import io
import json
import logging
import uuid
from datetime import UTC, datetime

import feedparser
import httpx
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

import vertexai
from google.cloud import storage, texttospeech
from supabase import Client, create_client
from vertexai.generative_models import GenerativeModel


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

    async def process_newsletter(self, url: str, issue_id: str | None = None) -> str:
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

        # Delete old groups (cascades to segments) if reprocessing
        self.supabase.table("topic_groups").delete().eq("issue_id", issue_id).execute()

        # Group segments
        groups = self._group_segments(segments_data)
        logger.info(f"Created {len(groups)} topic groups")

        # Process groups in parallel
        semaphore = asyncio.Semaphore(self.max_concurrent_segments) # Reuse existing semaphore setting

        async def process_group(group: dict) -> dict:
            async with semaphore:
                group["issue_id"] = issue_id
                
                # 1. Prepare texts for cleaning
                # Include label as first item if present
                texts_to_clean = []
                if group["label"]:
                    texts_to_clean.append(group["label"])
                
                for seg in group["segments"]:
                    texts_to_clean.append(seg["content_raw"])
                
                # 2. Batch clean texts
                cleaned_texts = await self._clean_texts_batch(texts_to_clean)
                
                # 3. Assign back to content and prepare for audio
                # Handle label
                final_audio_texts = []
                idx_offset = 0
                
                if group["label"]:
                    # Label is the first cleaned text
                    # We can prefix it with "Now:" or similar if needed, but Gemini handles cleaning
                    final_audio_texts.append(cleaned_texts[0])
                    idx_offset = 1
                
                # Handle segments
                for i, seg in enumerate(group["segments"]):
                    clean = cleaned_texts[i + idx_offset]
                    seg["content_clean"] = clean
                    final_audio_texts.append(clean)
                
                # 4. Generate Combined Audio (Step 5)
                # Concatenate with pauses
                # Using triple dot ... or explicit break logic in cleaning
                combined_text = " ... ".join(final_audio_texts)
                
                audio_url, duration_ms = await self._generate_audio(
                    combined_text, issue_id, group["order_index"]
                )
                
                group["audio_url"] = audio_url
                group["audio_duration_ms"] = duration_ms
                
                return group

        # Execute group processing
        processed_groups = []
        failed_groups = []
        tasks = [process_group(g) for g in groups]

        for future in asyncio.as_completed(tasks):
            try:
                p_group = await future
                processed_groups.append(p_group)
                logger.info(f"Processed group {p_group['order_index']}")
            except Exception as e:
                failed_groups.append(str(e))
                logger.error(f"Failed to process group: {e}")

        # Check if too many groups failed (more than 50%)
        if failed_groups and len(failed_groups) > len(groups) / 2:
            raise RuntimeError(
                f"Too many groups failed ({len(failed_groups)}/{len(groups)}): {failed_groups[:3]}"
            )

        if failed_groups:
            logger.warning(
                f"{len(failed_groups)}/{len(groups)} groups failed, continuing with {len(processed_groups)} successful groups"
            )

        # Sort by order_index to be safe
        processed_groups.sort(key=lambda x: x["order_index"])

        # Insert into DB
        # 1. Insert Groups
        groups_payload = [{
            "issue_id": issue_id,
            "label": g["label"],
            "audio_url": g["audio_url"],
            "audio_duration_ms": g["audio_duration_ms"],
            "order_index": g["order_index"]
        } for g in processed_groups]

        if groups_payload:
            groups_resp = self.supabase.table("topic_groups").insert(groups_payload).execute()
            inserted_groups = groups_resp.data

            # Validate all groups were inserted
            if len(inserted_groups) != len(groups_payload):
                logger.error(
                    f"Inserted {len(inserted_groups)} groups, expected {len(groups_payload)}"
                )

            # Create a map of order_index -> group_id (safe key, not relying on insertion order)
            group_id_map = {g["order_index"]: g["id"] for g in inserted_groups}

            # Prepare Segments
            all_segments = []
            for g in processed_groups:
                g_id = group_id_map.get(g["order_index"])
                if g_id is None:
                    logger.error(f"No group_id found for order_index {g['order_index']}, skipping segments")
                    continue
                for seg in g["segments"]:
                    seg["issue_id"] = issue_id
                    seg["topic_group_id"] = g_id
                    # Ensure all required fields
                    if "content_clean" not in seg:
                        seg["content_clean"] = seg["content_raw"]
                    all_segments.append(seg)
            
            # 3. Batch Insert Segments
            if all_segments:
                 # Batch insert
                batch_size = 50
                for i in range(0, len(all_segments), batch_size):
                    batch = all_segments[i:i + batch_size]
                    self.supabase.table("segments").insert(batch).execute()
                logger.info(f"Inserted {len(all_segments)} segments for issue {issue_id}")

        # Mark issue as processed
        self.supabase.table("issues").update(
            {"processed_at": datetime.now(UTC).isoformat()}
        ).eq("id", issue_id).execute()

        logger.info(f"Newsletter processing complete: {issue_id}")
        return issue_id

    async def _fetch_newsletter(self, url: str) -> str:
        """Fetch newsletter content from URL."""
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_newsletter(self, html_content: str, url: str) -> tuple[dict, list[dict]]:
        """
        Parse newsletter HTML into structured segments.
        Supports various formats (Substack, Buttondown, generic blogs) by detecting
        common content containers and headers.

        Args:
            html_content: Raw HTML
            url: Newsletter URL

        Returns:
            tuple: (issue_data, segments_data)
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract issue metadata
        title_tag = soup.find("title")
        # Try to find h1 as title if title tag is generic
        h1 = soup.find("h1")
        
        title = "Untitled Newsletter"
        if title_tag and title_tag.text.strip():
            title = title_tag.text.strip()
        elif h1 and h1.text.strip():
            title = h1.text.strip()

        published_at = datetime.now(UTC).isoformat()

        issue_data = {
            "title": title,
            "url": url,
            "published_at": published_at,
        }

        # 1. Detect Main Content Container
        # Priority: <article> -> common content classes -> <body>
        article = soup.find("article")
        
        if not article:
            content_classes = [
                "content", "entry-content", "post-content", "main-content", 
                "newsletter-content", "issue-content", "main"
            ]
            for cls in content_classes:
                article = soup.find("div", class_=lambda x, c=cls: x and c in x)
                if article:
                    break
        
        if not article:
            article = soup.find("body")

        if not article:
            # Last resort
            article = soup

        segments_data = []
        order_index = 0
        
        # 2. Iterate through elements to build segments
        # We want to segment by Headers (H1-H4)
        # Everything between headers belongs to the previous header's group (conceptually)
        # But here we just flatten into segments: Header Segment -> Item Segment -> Item Segment...
        
        # Helper to add segment
        def add_segment(text, seg_type, links=None):
            nonlocal order_index
            if not text:
                return
            segments_data.append({
                "segment_type": seg_type,
                "content_raw": text,
                "links": links or [],
                "order_index": order_index,
            })
            order_index += 1

        # Flatten the interesting elements
        # We look for direct children or just all relevant tags in order?
        # Traversing all tags in order is safer for preservation
        
        # Tags we care about for content
        content_tags = ["p", "li", "div", "blockquote"]
        header_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
        
        for element in article.find_all(header_tags + content_tags):
            # Skip if inside another element we already processed? 
            # find_all returns nested elements too.
            
            # Fix duplication: If this element acts as a container for other interesting elements,
            # let the loop handle the children instead.
            if element.name in ["div", "blockquote", "li"]:
                # If this element contains any of our target tags, skip it to avoid double-counting
                # (e.g. skip the DIV so we can process the P inside it)
                if element.find(header_tags + content_tags):
                    continue

            # Get text content
            text = element.get_text(strip=True)
            if not text:
                continue

            # Skip elements that are likely menus or footers based on class/id
            # (Simple naive check)
            cls_str = " ".join(element.get("class", []))
            if any(x in cls_str for x in ["nav", "menu", "footer", "subscribe", "button", "share"]):
                continue

            if element.name in header_tags:
                add_segment(text, "section_header")
            
            elif element.name in content_tags:
                # Heuristic: Check if it looks like a header (short, strong, no punctuation at end?)
                # AINews specific: <p><strong>Topic</strong></p>
                is_header_like = False
                if element.name == "p":
                    strong = element.find("strong")
                    if strong and strong.get_text(strip=True) == text:
                        is_header_like = True
                
                if is_header_like:
                    add_segment(text, "topic_header")
                else:
                    # It's content
                    # Extract links
                    links = [
                        {"text": a.get_text(strip=True), "url": a.get("href")}
                        for a in element.find_all("a")
                        if a.get("href")
                    ]
                    
                    # For long content, we might want to split or just keep as one item
                    # Filter out very short UI text
                    if len(text) > 10:
                        add_segment(text, "item", links)

        # 3. Fallback: If no segments found (e.g. text directly in div), grab all text
        if not segments_data:
            text = article.get_text(strip=True)
            if text:
                add_segment(text[:100] + "...", "section_header") # Fake header
                add_segment(text, "item")

        return issue_data, segments_data

    def _group_segments(self, segments_data: list[dict]) -> list[dict]:
        """
        Group segments into topic groups.
        Topic Headers and Section Headers start new groups and become labels.
        Items follow the preceding header.
        """
        groups = []
        current_group = None
        group_order = 0
        
        for seg in segments_data:
            stype = seg["segment_type"]
            
            if stype in ["topic_header", "section_header"]:
                # Start new group using this header as label
                current_group = {
                    "label": seg["content_raw"],
                    "segments": [],
                    "order_index": group_order,
                    "audio_url": None,
                    "audio_duration_ms": 0
                }
                groups.append(current_group)
                group_order += 1
            
            elif stype == "item":
                if current_group is None:
                    # Create anonymous group for loose items
                    current_group = {
                        "label": "General",
                        "segments": [],
                        "order_index": group_order,
                        "audio_url": None,
                        "audio_duration_ms": 0
                    }
                    groups.append(current_group)
                    group_order += 1
                
                current_group["segments"].append(seg)
        
        # Filter out empty groups (headers with no items waste API calls)
        groups = [g for g in groups if g["segments"]]

        # Re-index after filtering
        for i, g in enumerate(groups):
            g["order_index"] = i

        return groups

    async def _clean_texts_batch(self, texts: list[str]) -> list[str]:
        """
        Clean a list of texts using Gemini in one call.
        """
        if not texts:
            return []

        prompt = """
Clean the following list of newsletter texts for text-to-speech.
Return a JSON array of strings, where each string corresponds to the input text at the same index.

Rules:
1. Replace "@username" with "[username] tweeted"
2. Replace "/r/subreddit" with "the [subreddit] subreddit"
3. For markdown links [text](url), keep only the text
4. If a text seems to be a header, keep it conversational (e.g. prefix with "Now:")
5. Keep natural
6. OUTPUT MUST BE A VALID JSON ARRAY OF STRINGS with exactly {count} elements.

<texts_to_clean>
{texts_json}
</texts_to_clean>
""".format(texts_json=json.dumps(texts), count=len(texts))

        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            # Parse response, handling potential markdown wrapping
            response_text = response.text.strip()
            if response_text.startswith("```"):
                # Remove markdown code block wrapper
                lines = response_text.split("\n")
                # Remove first line (```json) and last line (```)
                response_text = "\n".join(lines[1:-1])

            cleaned = json.loads(response_text)

            # Validate response length matches input
            if not isinstance(cleaned, list):
                logger.error(f"Gemini returned non-list: {type(cleaned)}. Returning raw texts.")
                return texts

            if len(cleaned) != len(texts):
                logger.error(
                    f"Gemini returned {len(cleaned)} items, expected {len(texts)}. Returning raw texts."
                )
                return texts

            return cleaned
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}. Returning raw texts.")
            return texts
        except Exception as e:
            logger.error(f"Batch cleaning failed: {e}. Returning raw texts.")
            return texts


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

    async def ask(self, question: str, issue_id: str, group_id: str) -> tuple[str, str]:
        """
        Answer a question about a specific topic group in a newsletter issue.
        
        Args:
            question: User's question
            issue_id: Issue UUID
            group_id: Topic Group UUID
            
        Returns:
            tuple: (answer_text, audio_url)
        """
        # 1. Fetch context (segments) for the group
        segments_resp = self.supabase.table("segments") \
            .select("content_clean, content_raw") \
            .eq("topic_group_id", group_id) \
            .order("order_index") \
            .execute()
            
        if not segments_resp.data:
            return "I couldn't find the content for this section.", ""
            
        # Combine text
        context_text = "\n".join([
            s.get("content_clean") or s.get("content_raw", "") 
            for s in segments_resp.data
        ])
        
        # 2. Call Gemini
        prompt = f"""
You are an AI assistant helping a user listen to a newsletter.
The user is listening to a section with the following content:

<content>
{context_text}
</content>

The user asks: "{question}"

Answer the question based ONLY on the content above. 
Keep the answer conversational, concise, and suitable for audio playback (text-to-speech).
Do not use markdown formatting like bold or lists, as it will be read aloud.
If the answer is not in the content, say so politely.
"""
        response = await asyncio.to_thread(
            self.gemini_model.generate_content,
            prompt
        )
        answer_text = response.text.strip()
        
        # 3. Generate Audio
        # Use a unique ID for the Q&A audio file
        qa_id = str(uuid.uuid4())
        
        # We'll use a specific folder for Q&A
        blob_name = f"{issue_id}/qna/{qa_id}.mp3"
        
        synthesis_input = texttospeech.SynthesisInput(text=answer_text)
        
        # Generate audio
        tts_response = await asyncio.to_thread(
            self.tts_client.synthesize_speech,
            input=synthesis_input,
            voice=self.voice,
            audio_config=self.audio_config,
        )

        bucket = self.storage_client.bucket(self.gcs_bucket_name)
        blob = bucket.blob(blob_name)

        await asyncio.to_thread(
            blob.upload_from_string,
            tts_response.audio_content,
            content_type="audio/mpeg",
        )

        # Make blob public or generate signed URL
        blob.make_public()
        audio_url = blob.public_url
        
        return answer_text, audio_url

    async def get_issue_status(self, issue_id: str) -> dict | None:
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

    async def fetch_latest_newsletter_url(self) -> str | None:
        """
        Fetch the latest newsletter URL from the AINews RSS feed.
        
        This method is used by Cloud Scheduler to discover new issues
        without hardcoding URLs in the scheduler configuration.

        Returns:
            str: URL of the latest newsletter issue, or None if fetch fails
        """
        rss_url = "https://news.smol.ai/rss.xml"
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
