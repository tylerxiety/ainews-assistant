#!/usr/bin/env python3
"""
Backfill Chinese translations and audio for the latest issue.

Usage:
    cd backend && uv run scripts/backfill_chinese.py
    cd backend && uv run scripts/backfill_chinese.py --n-segments 5 --strategy shortest
"""
import argparse
import asyncio

from _common import get_processor, setup_logging

logger = setup_logging()


async def backfill_chinese(n_segments: int | None = None, strategy: str = "first"):
    """
    Backfill Chinese translations and audio for the latest issue.

    Args:
        n_segments: Optional limit on number of segments to process (for testing)
        strategy: Selection strategy - "first" (default) or "shortest" (for showcase)

    Returns:
        dict: Backfill status with counts of processed segments
    """
    processor = get_processor()

    try:
        # 1. Find the latest processed issue
        issues_resp = processor.supabase.table("issues") \
            .select("id, title") \
            .not_.is_("processed_at", "null") \
            .order("processed_at", desc=True) \
            .limit(1) \
            .execute()

        if not issues_resp.data:
            logger.error("No processed issues found")
            return {"status": "error", "message": "No processed issues found"}

        issue_id = issues_resp.data[0]["id"]
        issue_title = issues_resp.data[0]["title"]
        logger.info(f"Backfilling Chinese for issue: {issue_title} ({issue_id})")

        # 2. Fetch segments that need Chinese content
        segments_resp = processor.supabase.table("segments") \
            .select("id, content_raw, content_clean, topic_group_id, order_index") \
            .eq("issue_id", issue_id) \
            .is_("content_raw_zh", "null") \
            .order("order_index") \
            .execute()

        segments = segments_resp.data
        if not segments:
            logger.info("All segments already have Chinese content")
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "All segments already have Chinese content"
            }

        # Apply selection strategy and limit
        if strategy == "shortest":
            # Sort by content length (shortest first) - better for TTS reliability
            segments = sorted(segments, key=lambda s: len(s.get("content_raw", "")))
            logger.info("Using 'shortest' strategy - selecting shortest segments")

        if n_segments is not None:
            segments = segments[:n_segments]
            logger.info(f"Limited to {n_segments} segments ({strategy} strategy)")

        # 3. Fetch all topic groups (for order_index lookup and Chinese labels)
        all_groups_resp = processor.supabase.table("topic_groups") \
            .select("id, label, label_zh, order_index") \
            .eq("issue_id", issue_id) \
            .execute()

        # Build lookup maps
        group_order_map = {g["id"]: g["order_index"] for g in all_groups_resp.data}
        groups = {g["id"]: g["label"] for g in all_groups_resp.data if g.get("label_zh") is None}

        # 4. Batch translate content_raw
        content_raw_list = [s["content_raw"] for s in segments]
        translated_raw = await processor._translate_texts_batch(content_raw_list)

        # 5. Clean translated texts for TTS
        texts_to_clean = [t for t in translated_raw if t is not None]
        if texts_to_clean:
            cleaned_zh = await processor._clean_texts_batch(texts_to_clean)
            cleaned_zh_iter = iter(cleaned_zh)
            translated_clean = [
                next(cleaned_zh_iter) if t is not None else None
                for t in translated_raw
            ]
        else:
            translated_clean = [None] * len(translated_raw)

        # 6. Translate group labels
        unique_labels = list(set(groups.values()))
        if unique_labels:
            translated_labels = await processor._translate_texts_batch(unique_labels)
            label_map = dict(zip(unique_labels, translated_labels, strict=True))
        else:
            label_map = {}

        # 7. Generate Chinese audio and update segments
        processed_count = 0
        failed_count = 0

        for i, seg in enumerate(segments):
            raw_zh = translated_raw[i]
            clean_zh = translated_clean[i]

            if not clean_zh:
                logger.warning(f"No Chinese translation for segment {seg['id']}")
                failed_count += 1
                continue

            # Get group_order from pre-fetched map
            group_order = group_order_map.get(seg.get("topic_group_id"), 0)

            # Generate Chinese audio
            try:
                audio_url_zh, duration_ms_zh = await processor._generate_audio(
                    clean_zh, issue_id, group_order, seg["order_index"], language="zh"
                )
            except Exception as e:
                logger.error(f"Failed to generate Chinese audio for segment {seg['id']}: {e}")
                failed_count += 1
                continue

            # Update segment in database
            processor.supabase.table("segments").update({
                "content_raw_zh": raw_zh,
                "content_clean_zh": clean_zh,
                "audio_url_zh": audio_url_zh,
                "audio_duration_ms_zh": duration_ms_zh
            }).eq("id", seg["id"]).execute()

            processed_count += 1
            logger.info(f"Backfilled segment {processed_count}/{len(segments)}")

        # 8. Update topic groups with Chinese labels
        groups_updated = 0
        for group_id, label in groups.items():
            label_zh = label_map.get(label)
            if label_zh:
                processor.supabase.table("topic_groups").update({
                    "label_zh": label_zh
                }).eq("id", group_id).execute()
                groups_updated += 1

        result = {
            "status": "completed",
            "issue_id": issue_id,
            "issue_title": issue_title,
            "segments_processed": processed_count,
            "segments_failed": failed_count,
            "groups_updated": groups_updated,
            "message": f"Backfilled Chinese content for {processed_count} segments"
        }
        logger.info(f"Result: {result}")
        return result

    finally:
        await processor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Chinese translations and audio for the latest issue."
    )
    parser.add_argument(
        "--n-segments",
        type=int,
        default=None,
        help="Limit number of segments to process (for testing)"
    )
    parser.add_argument(
        "--strategy",
        choices=["first", "shortest"],
        default="first",
        help="Selection strategy: 'first' (default) or 'shortest'"
    )
    args = parser.parse_args()

    result = asyncio.run(backfill_chinese(args.n_segments, args.strategy))
    print(f"\n{result['status'].upper()}: {result.get('message', '')}")


if __name__ == "__main__":
    main()
