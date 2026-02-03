#!/usr/bin/env python3
"""
Backfill Chinese audio for a specific section only (e.g., "AI Twitter Recap").

Usage:
    cd backend && uv run scripts/backfill_chinese_section.py
    cd backend && uv run scripts/backfill_chinese_section.py --section-name "AI Reddit Recap"
    cd backend && uv run scripts/backfill_chinese_section.py --issue-id <uuid>
"""
import argparse
import asyncio

from _common import get_processor, setup_logging

logger = setup_logging()


async def backfill_chinese_section(
    section_name: str = "AI Twitter Recap",
    issue_id: str | None = None
):
    """
    Backfill Chinese audio for a specific section only.

    Args:
        section_name: Name of the section to process (default: "AI Twitter Recap")
        issue_id: Optional specific issue. If not provided, processes the latest issue.

    Returns:
        dict: Backfill status with counts
    """
    processor = get_processor()

    try:
        # 1. Find the issue
        if issue_id:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title") \
                .eq("id", issue_id) \
                .single() \
                .execute()
            if not issues_resp.data:
                logger.error(f"Issue not found: {issue_id}")
                return {"status": "error", "message": "Issue not found"}
            issue = issues_resp.data
        else:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title") \
                .not_.is_("processed_at", "null") \
                .order("processed_at", desc=True) \
                .limit(1) \
                .execute()
            if not issues_resp.data:
                logger.error("No processed issues found")
                return {"status": "error", "message": "No processed issues found"}
            issue = issues_resp.data[0]

        issue_id = issue["id"]
        logger.info(f"Backfilling Chinese for section '{section_name}' in issue: {issue['title']}")

        # 2. Find the section header and next section header
        groups_resp = processor.supabase.table("topic_groups") \
            .select("id, label, order_index, is_section_header") \
            .eq("issue_id", issue_id) \
            .order("order_index") \
            .execute()

        groups = groups_resp.data
        if not groups:
            logger.error("No groups found for this issue")
            return {"status": "error", "message": "No groups found for this issue"}

        # Find section boundaries
        section_start_order = None
        section_end_order = None

        for i, g in enumerate(groups):
            if g.get("is_section_header") and section_name.lower() in g["label"].lower():
                section_start_order = g["order_index"]
                # Find next section header
                for j in range(i + 1, len(groups)):
                    if groups[j].get("is_section_header"):
                        section_end_order = groups[j]["order_index"]
                        break
                break

        if section_start_order is None:
            available_sections = [g['label'] for g in groups if g.get('is_section_header')]
            logger.error(f"Section '{section_name}' not found. Available: {available_sections}")
            return {
                "status": "error",
                "message": f"Section '{section_name}' not found. Available sections: {available_sections}"
            }

        # 3. Get topic groups in this section (between section headers)
        section_group_ids = []
        for g in groups:
            if g["order_index"] > section_start_order:
                if section_end_order and g["order_index"] >= section_end_order:
                    break
                if not g.get("is_section_header"):
                    section_group_ids.append(g["id"])

        if not section_group_ids:
            logger.info("No topic groups found in this section")
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "section_name": section_name,
                "message": "No topic groups found in this section"
            }

        logger.info(f"Found {len(section_group_ids)} topic groups in section '{section_name}'")

        # 4. Get segments in these groups that need Chinese content
        segments_resp = processor.supabase.table("segments") \
            .select("id, content_raw, content_clean, topic_group_id, order_index") \
            .in_("topic_group_id", section_group_ids) \
            .is_("content_raw_zh", "null") \
            .order("order_index") \
            .execute()

        segments = segments_resp.data
        if not segments:
            logger.info("All segments in this section already have Chinese content")
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "section_name": section_name,
                "message": "All segments in this section already have Chinese content"
            }

        logger.info(f"Processing {len(segments)} segments in section '{section_name}'")

        # 5. Batch translate
        content_raw_list = [s["content_raw"] for s in segments]
        translated_raw = await processor._translate_texts_batch(content_raw_list)

        # 6. Clean translated texts for TTS
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

        # 7. Generate Chinese audio and update segments
        # Build group_id -> order_index map
        group_order_map = {g["id"]: g["order_index"] for g in groups}

        processed_count = 0
        failed_count = 0

        for i, seg in enumerate(segments):
            raw_zh = translated_raw[i]
            clean_zh = translated_clean[i]

            if not clean_zh:
                logger.warning(f"No Chinese translation for segment {seg['id']}")
                failed_count += 1
                continue

            group_order = group_order_map.get(seg["topic_group_id"], 0)

            try:
                audio_url_zh, duration_ms_zh = await processor._generate_audio(
                    clean_zh, issue_id, group_order, seg["order_index"], language="zh"
                )
            except Exception as e:
                logger.error(f"Failed to generate Chinese audio for segment {seg['id']}: {e}")
                failed_count += 1
                continue

            # Update segment
            processor.supabase.table("segments").update({
                "content_raw_zh": raw_zh,
                "content_clean_zh": clean_zh,
                "audio_url_zh": audio_url_zh,
                "audio_duration_ms_zh": duration_ms_zh
            }).eq("id", seg["id"]).execute()

            processed_count += 1
            logger.info(f"Backfilled segment {processed_count}/{len(segments)}")

        result = {
            "status": "completed",
            "issue_id": issue_id,
            "issue_title": issue["title"],
            "section_name": section_name,
            "segments_processed": processed_count,
            "segments_failed": failed_count,
            "message": f"Backfilled Chinese audio for {processed_count} segments in '{section_name}'"
        }
        logger.info(f"Result: {result}")
        return result

    finally:
        await processor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Chinese audio for a specific section."
    )
    parser.add_argument(
        "--section-name",
        default="AI Twitter Recap",
        help="Name of the section to process (default: 'AI Twitter Recap')"
    )
    parser.add_argument(
        "--issue-id",
        default=None,
        help="Optional specific issue ID. If not provided, processes the latest issue."
    )
    args = parser.parse_args()

    result = asyncio.run(backfill_chinese_section(args.section_name, args.issue_id))
    print(f"\n{result['status'].upper()}: {result.get('message', '')}")


if __name__ == "__main__":
    main()
