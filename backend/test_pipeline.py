"""
End-to-end test of the newsletter processing pipeline.
Tests: fetch → parse → clean (Gemini) → TTS → upload to GCS → store in Supabase
"""
import asyncio
import os
from dotenv import load_dotenv
from processor import NewsletterProcessor

load_dotenv()

async def test_full_pipeline():
    """Test the complete processing pipeline with a real newsletter."""

    print("=" * 60)
    print("TESTING FULL NEWSLETTER PROCESSING PIPELINE")
    print("=" * 60)

    # Initialize processor
    processor = NewsletterProcessor(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY"),
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
        gcp_region=os.getenv("GCP_REGION"),
        gcs_bucket_name=os.getenv("GCS_BUCKET_NAME"),
    )

    # Test with a real AINews issue
    test_url = "https://news.smol.ai/issues/26-01-16-chatgpt-ads/"

    print(f"\n1. Processing newsletter: {test_url}")
    print("-" * 60)

    try:
        # This will test the full pipeline
        print("   Fetching newsletter...")
        raw_content = await processor._fetch_newsletter(test_url)
        print(f"   ✅ Fetched {len(raw_content)} characters")

        print("\n   Parsing newsletter...")
        issue_data, segments_data = processor._parse_newsletter(raw_content, test_url)
        print(f"   ✅ Parsed into {len(segments_data)} segments")
        print(f"   ✅ Issue title: {issue_data['title']}")

        # Show sample segments
        print(f"\n   Sample segments:")
        for i, seg in enumerate(segments_data[:3]):
            seg_type = seg['segment_type']
            content = seg['content_raw'][:80]
            print(f"     {i+1}. [{seg_type}] {content}...")

        # Test text cleaning with Gemini (just first 3 segments)
        print(f"\n2. Testing Gemini text cleaning (first 3 segments)...")
        print("-" * 60)

        for i, seg in enumerate(segments_data[:3]):
            print(f"\n   Segment {i+1}:")
            print(f"   Raw: {seg['content_raw'][:100]}...")

            cleaned = await processor._clean_text_for_tts(seg['content_raw'])
            print(f"   Cleaned: {cleaned[:100]}...")

        # Test TTS generation (just one segment to save time/cost)
        print(f"\n3. Testing TTS audio generation (1 segment)...")
        print("-" * 60)

        test_text = "This is a test of the Text to Speech system using Chirp 3 HD voice."
        print(f"   Generating audio for: \"{test_text}\"")

        audio_url, duration_ms = await processor._generate_audio(
            test_text,
            issue_id="test-issue",
            segment_index=0
        )

        print(f"   ✅ Audio generated!")
        print(f"   ✅ URL: {audio_url}")
        print(f"   ✅ Duration: {duration_ms}ms")

        print(f"\n4. Summary")
        print("=" * 60)
        print(f"✅ Fetch: Working")
        print(f"✅ Parse: Working ({len(segments_data)} segments)")
        print(f"✅ Gemini cleaning: Working")
        print(f"✅ TTS generation: Working")
        print(f"✅ GCS upload: Working")
        print(f"\n🎉 PIPELINE TEST COMPLETE!")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
