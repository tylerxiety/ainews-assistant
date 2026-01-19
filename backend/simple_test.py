"""
Simple test that processes just 3 segments with progress updates.
"""
import asyncio
import os
from dotenv import load_dotenv
from processor import NewsletterProcessor

load_dotenv()

async def test_simple():
    """Test with just 3 segments."""

    print("🚀 Starting simple test (3 segments only)...")
    print("=" * 60)

    processor = NewsletterProcessor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY"),
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
        gcp_region=os.getenv("GCP_REGION"),
        gcs_bucket_name=os.getenv("GCS_BUCKET_NAME"),
    )

    url = "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"

    # Fetch
    print("\n1. Fetching newsletter...")
    raw_content = await processor._fetch_newsletter(url)
    print(f"   ✅ Fetched {len(raw_content)} bytes")

    # Parse
    print("\n2. Parsing...")
    issue_data, segments_data = processor._parse_newsletter(raw_content, url)
    print(f"   ✅ Found {len(segments_data)} total segments")

    # Limit to 3
    segments_data = segments_data[:3]
    print(f"   ✅ Testing with first 3 segments")

    # Check existing issue
    print("\n3. Checking database...")
    existing = processor.supabase.table("issues").select("*").eq("url", url).execute()

    if existing.data:
        issue_id = existing.data[0]["id"]
        print(f"   ✅ Found existing issue: {issue_id}")
        print(f"   🗑️  Deleting old segments...")
        processor.supabase.table("segments").delete().eq("issue_id", issue_id).execute()
    else:
        print(f"   ✅ Creating new issue...")
        result = processor.supabase.table("issues").insert(issue_data).execute()
        issue_id = result.data[0]["id"]
        print(f"   ✅ Created: {issue_id}")

    # Process each segment
    print(f"\n4. Processing segments...")
    for i, segment in enumerate(segments_data, 1):
        print(f"\n   Segment {i}/3:")
        print(f"   Content: {segment['content_raw'][:60]}...")

        segment["issue_id"] = issue_id

        print(f"   🤖 Cleaning with Gemini...")
        clean_text = await processor._clean_text_for_tts(segment["content_raw"])
        segment["content_clean"] = clean_text
        print(f"   ✅ Cleaned: {clean_text[:60]}...")

        print(f"   🎵 Generating audio...")
        audio_url, duration_ms = await processor._generate_audio(
            clean_text, issue_id, segment["order_index"]
        )
        segment["audio_url"] = audio_url
        segment["audio_duration_ms"] = duration_ms
        print(f"   ✅ Audio: {audio_url}")

    # Store
    print(f"\n5. Storing in database...")
    processor.supabase.table("segments").insert(segments_data).execute()
    processor.supabase.table("issues").update(
        {"processed_at": __import__("datetime").datetime.utcnow().isoformat()}
    ).eq("id", issue_id).execute()
    print(f"   ✅ Stored!")

    print("\n" + "=" * 60)
    print("🎉 SUCCESS!")
    print(f"Issue ID: {issue_id}")
    print(f"Segments: 3")
    print(f"\nCheck Supabase:")
    print(f"https://supabase.com/dashboard/project/akxytmuwjomxlneqzgic/editor")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_simple())
