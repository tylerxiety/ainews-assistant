#!/usr/bin/env python3
"""
Test processing of newsletters with limited scope.

Two modes:
- Legacy mode (--legacy): Process only first 10 segments
- Groups mode (default): Process only first N topic groups

Usage:
    cd backend && uv run scripts/process_test.py --url "https://buttondown.com/ainews/..."
    cd backend && uv run scripts/process_test.py --url "..." --num-groups 3
    cd backend && uv run scripts/process_test.py --url "..." --legacy
"""
import argparse
import asyncio
from datetime import UTC, datetime

from _common import get_processor, setup_logging

logger = setup_logging()


async def process_test_legacy(url: str):
    """
    Process only first 10 segments (legacy mode).
    """
    processor = get_processor()

    try:
        # Fetch and parse
        raw_content = await processor._fetch_newsletter(url)
        issue_data, segments_data = processor._parse_newsletter(raw_content, url)

        # Limit to first 10 segments
        segments_data = segments_data[:10]

        # Upsert issue to handle race conditions
        issue_result = processor.supabase.table("issues").upsert(
            issue_data,
            on_conflict="url"
        ).execute()
        issue_id = issue_result.data[0]["id"]

        # Delete old segments if reprocessing
        processor.supabase.table("segments").delete().eq("issue_id", issue_id).execute()

        # Process segments
        for segment in segments_data:
            segment["issue_id"] = issue_id
            clean_text = await processor._clean_text_for_tts(segment["content_raw"])
            segment["content_clean"] = clean_text

            audio_url, duration_ms = await processor._generate_audio(
                clean_text, issue_id, 0, segment["order_index"]
            )
            segment["audio_url"] = audio_url
            segment["audio_duration_ms"] = duration_ms

        # Store segments
        processor.supabase.table("segments").insert(segments_data).execute()

        # Mark as processed
        processor.supabase.table("issues").update(
            {"processed_at": datetime.now(UTC).isoformat()}
        ).eq("id", issue_id).execute()

        result = {
            "status": "completed",
            "issue_id": issue_id,
            "segments_processed": len(segments_data),
            "message": "Test processing complete (first 10 segments only)"
        }
        logger.info(f"Result: {result}")
        return result

    finally:
        await processor.close()


async def process_test_groups(url: str, num_groups: int = 2):
    """
    Process only first N topic groups.
    """
    processor = get_processor()

    try:
        # Fetch and parse
        raw_content = await processor._fetch_newsletter(url)
        issue_data, segments_data = processor._parse_newsletter(raw_content, url)

        # Group segments
        groups = processor._group_segments(segments_data)
        logger.info(f"Total groups found: {len(groups)}")

        # Limit to first N groups
        groups = groups[:num_groups]
        # Re-index
        for i, g in enumerate(groups):
            g["order_index"] = i

        logger.info(f"Processing {len(groups)} groups")

        # Upsert issue
        issue_result = processor.supabase.table("issues").upsert(
            issue_data,
            on_conflict="url"
        ).execute()
        issue_id = issue_result.data[0]["id"]

        # Delete old groups and segments if reprocessing
        processor.supabase.table("topic_groups").delete().eq("issue_id", issue_id).execute()

        # Process each group
        semaphore = asyncio.Semaphore(processor.max_concurrent_segments)

        async def process_group(group):
            async with semaphore:
                group["issue_id"] = issue_id

                # Prepare texts for cleaning
                texts_to_clean = []
                if group["label"]:
                    texts_to_clean.append(group["label"])
                for seg in group["segments"]:
                    texts_to_clean.append(seg["content_raw"])

                # Batch clean texts
                cleaned_texts = await processor._clean_texts_batch(texts_to_clean)

                # Assign back and prepare for audio
                final_audio_texts = []
                idx_offset = 0

                if group["label"]:
                    final_audio_texts.append(cleaned_texts[0])
                    idx_offset = 1

                for i, seg in enumerate(group["segments"]):
                    clean = cleaned_texts[i + idx_offset]
                    seg["content_clean"] = clean
                    final_audio_texts.append(clean)

                # Generate combined audio
                combined_text = " ... ".join(final_audio_texts)
                audio_url, duration_ms = await processor._generate_audio(
                    combined_text, issue_id, group["order_index"], 0
                )

                group["audio_url"] = audio_url
                group["audio_duration_ms"] = duration_ms

                return group

        # Execute
        tasks = [process_group(g) for g in groups]
        processed_groups = []

        for future in asyncio.as_completed(tasks):
            try:
                p_group = await future
                processed_groups.append(p_group)
                logger.info(f"Processed group {p_group['order_index']}: {p_group['label'][:50]}...")
            except Exception as e:
                logger.error(f"Failed to process group: {e}")

        processed_groups.sort(key=lambda x: x["order_index"])

        # Insert groups
        groups_payload = [{
            "issue_id": issue_id,
            "label": g["label"],
            "audio_url": g["audio_url"],
            "audio_duration_ms": g["audio_duration_ms"],
            "order_index": g["order_index"]
        } for g in processed_groups]

        total_segments = 0
        if groups_payload:
            groups_resp = processor.supabase.table("topic_groups").insert(groups_payload).execute()
            inserted_groups = groups_resp.data

            group_id_map = {g["order_index"]: g["id"] for g in inserted_groups}

            # Prepare and insert segments
            all_segments = []
            for g in processed_groups:
                g_id = group_id_map.get(g["order_index"])
                if g_id is None:
                    continue
                for seg in g["segments"]:
                    seg["issue_id"] = issue_id
                    seg["topic_group_id"] = g_id
                    if "content_clean" not in seg:
                        seg["content_clean"] = seg["content_raw"]
                    all_segments.append(seg)

            if all_segments:
                processor.supabase.table("segments").insert(all_segments).execute()
                total_segments = len(all_segments)

        # Mark as processed
        processor.supabase.table("issues").update(
            {"processed_at": datetime.now(UTC).isoformat()}
        ).eq("id", issue_id).execute()

        result = {
            "status": "completed",
            "issue_id": issue_id,
            "groups_processed": len(processed_groups),
            "segments_processed": total_segments,
            "groups_detail": [{"label": g["label"][:60], "segments": len(g["segments"])} for g in processed_groups],
            "message": f"Test processing complete (first {num_groups} topic groups)"
        }
        logger.info(f"Result: {result}")
        return result

    finally:
        await processor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Test processing of newsletters with limited scope."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the newsletter to process"
    )
    parser.add_argument(
        "--num-groups",
        type=int,
        default=2,
        help="Number of topic groups to process (default: 2)"
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy mode: process first 10 segments instead of groups"
    )
    args = parser.parse_args()

    if args.legacy:
        result = asyncio.run(process_test_legacy(args.url))
    else:
        result = asyncio.run(process_test_groups(args.url, args.num_groups))

    print(f"\n{result['status'].upper()}: {result.get('message', '')}")


if __name__ == "__main__":
    main()
