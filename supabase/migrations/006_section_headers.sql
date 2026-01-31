-- Add is_section_header flag to topic_groups
ALTER TABLE topic_groups ADD COLUMN IF NOT EXISTS is_section_header BOOLEAN DEFAULT FALSE;

-- Add Chinese audio columns for section headers (section headers store audio at group level, not segment level)
ALTER TABLE topic_groups ADD COLUMN IF NOT EXISTS audio_url_zh TEXT;
ALTER TABLE topic_groups ADD COLUMN IF NOT EXISTS audio_duration_ms_zh INTEGER;

-- Index for filtering section headers
CREATE INDEX IF NOT EXISTS idx_topic_groups_is_section_header ON topic_groups(is_section_header);

-- Function to increment order_index for groups at or after a given position (used for backfill insertion)
CREATE OR REPLACE FUNCTION increment_order_index(p_issue_id UUID, p_min_order INTEGER)
RETURNS void AS $$
BEGIN
    UPDATE topic_groups
    SET order_index = order_index + 1
    WHERE issue_id = p_issue_id AND order_index >= p_min_order;
END;
$$ LANGUAGE plpgsql;

COMMENT ON COLUMN topic_groups.is_section_header IS 'True for top-level section headers (e.g., AI Twitter Recap), false for topic headers';
COMMENT ON COLUMN topic_groups.audio_url_zh IS 'Chinese audio URL (used by section headers which have no segments)';
COMMENT ON COLUMN topic_groups.audio_duration_ms_zh IS 'Chinese audio duration in ms (used by section headers)';
