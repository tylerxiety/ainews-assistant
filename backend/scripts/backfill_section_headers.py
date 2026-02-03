#!/usr/bin/env python3
"""
Backfill section headers for existing newsletters.

Re-parses the newsletter HTML to identify section headers
(like "AI Twitter Recap", "AI Reddit Recap") and inserts them as topic_groups
with is_section_header=true.

Usage:
    cd backend && uv run scripts/backfill_section_headers.py
    cd backend && uv run scripts/backfill_section_headers.py --issue-id <uuid>
"""
import argparse
import asyncio

from _common import get_processor, setup_logging

logger = setup_logging()


async def backfill_section_headers(issue_id: str | None = None):
    """
    Backfill section headers for existing newsletters.

    Args:
        issue_id: Optional specific issue to backfill. If not provided, processes the latest issue.

    Returns:
        dict: Backfill status with counts of section headers added
    """
    processor = get_processor()

    try:
        # Find the issue to backfill
        if issue_id:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title, url") \
                .eq("id", issue_id) \
                .single() \
                .execute()
            if not issues_resp.data:
                logger.error(f"Issue not found: {issue_id}")
                return {"status": "error", "message": "Issue not found"}
            issue = issues_resp.data
        else:
            issues_resp = processor.supabase.table("issues") \
                .select("id, title, url") \
                .not_.is_("processed_at", "null") \
                .order("processed_at", desc=True) \
                .limit(1) \
                .execute()
            if not issues_resp.data:
                logger.error("No processed issues found")
                return {"status": "error", "message": "No processed issues found"}
            issue = issues_resp.data[0]

        issue_id = issue["id"]
        issue_url = issue["url"]
        logger.info(f"Backfilling section headers for issue: {issue['title']} ({issue_id})")

        # Fetch and re-parse the newsletter
        raw_content = await processor._fetch_newsletter(issue_url)
        _, segments_data = processor._parse_newsletter(raw_content, issue_url)

        # Group segments to identify section headers
        groups = processor._group_segments(segments_data)

        # Find section headers
        section_headers = [g for g in groups if g.get("is_section_header")]
        if not section_headers:
            logger.info("No section headers found in this newsletter")
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "No section headers found in this newsletter"
            }

        # Get existing groups to find insertion points
        existing_groups_resp = processor.supabase.table("topic_groups") \
            .select("id, label, order_index") \
            .eq("issue_id", issue_id) \
            .order("order_index") \
            .execute()

        existing_groups = existing_groups_resp.data
        if not existing_groups:
            logger.info("No existing groups found for this issue")
            return {
                "status": "skipped",
                "issue_id": issue_id,
                "message": "No existing groups found for this issue"
            }

        # Build a map of label -> existing group for matching
        existing_by_label = {g["label"]: g for g in existing_groups}

        # For each section header, find where it should be inserted
        # by looking at the topic that follows it in the parsed data
        headers_added = 0
        for sh in section_headers:
            sh_label = sh["label"]
            sh_order = sh["order_index"]

            # Check if this section header already exists
            if sh_label in existing_by_label:
                logger.info(f"Section header '{sh_label}' already exists, skipping")
                continue

            # Find the next non-section-header group in parsed data
            next_topic = None
            for g in groups:
                if g["order_index"] > sh_order and not g.get("is_section_header"):
                    next_topic = g
                    break

            if next_topic and next_topic["label"] in existing_by_label:
                # Insert before this topic
                insert_before_order = existing_by_label[next_topic["label"]]["order_index"]
            else:
                # Insert at the end
                insert_before_order = max(g["order_index"] for g in existing_groups) + 1

            # Shift existing groups to make room
            processor.supabase.rpc(
                "increment_order_index",
                {"p_issue_id": issue_id, "p_min_order": insert_before_order}
            ).execute()

            # Generate audio for section header
            cleaned_labels = await processor._clean_texts_batch([sh_label])
            translated_labels = await processor._translate_texts_batch([sh_label])
            label_text_en = cleaned_labels[0] if cleaned_labels else sh_label
            label_zh = translated_labels[0] if translated_labels else None

            # Clean translated label for TTS
            label_text_zh = None
            if label_zh:
                cleaned_zh = await processor._clean_texts_batch([label_zh])
                label_text_zh = cleaned_zh[0] if cleaned_zh else None

            # Generate English audio
            audio_url, duration_ms = await processor._generate_audio(
                label_text_en, issue_id, insert_before_order, 0, language="en"
            )

            # Generate Chinese audio
            audio_url_zh, duration_ms_zh = None, None
            if label_text_zh:
                try:
                    audio_url_zh, duration_ms_zh = await processor._generate_audio(
                        label_text_zh, issue_id, insert_before_order, 0, language="zh"
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate Chinese audio for section header: {e}")

            # Insert section header
            processor.supabase.table("topic_groups").insert({
                "issue_id": issue_id,
                "label": sh_label,
                "label_zh": label_zh,
                "audio_url": audio_url,
                "audio_duration_ms": duration_ms,
                "audio_url_zh": audio_url_zh,
                "audio_duration_ms_zh": duration_ms_zh,
                "order_index": insert_before_order,
                "is_section_header": True
            }).execute()

            headers_added += 1
            logger.info(f"Added section header: {sh_label}")

            # Refresh existing groups map
            existing_groups_resp = processor.supabase.table("topic_groups") \
                .select("id, label, order_index") \
                .eq("issue_id", issue_id) \
                .order("order_index") \
                .execute()
            existing_by_label = {g["label"]: g for g in existing_groups_resp.data}

        result = {
            "status": "completed",
            "issue_id": issue_id,
            "issue_title": issue["title"],
            "section_headers_added": headers_added,
            "message": f"Added {headers_added} section headers"
        }
        logger.info(f"Result: {result}")
        return result

    finally:
        await processor.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill section headers for existing newsletters."
    )
    parser.add_argument(
        "--issue-id",
        default=None,
        help="Optional specific issue ID. If not provided, processes the latest issue."
    )
    args = parser.parse_args()

    result = asyncio.run(backfill_section_headers(args.issue_id))
    print(f"\n{result['status'].upper()}: {result.get('message', '')}")


if __name__ == "__main__":
    main()
