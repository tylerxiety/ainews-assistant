-- Add bilingual (Chinese) content columns

-- Add Chinese content columns to segments table
ALTER TABLE segments
ADD COLUMN IF NOT EXISTS content_raw_zh TEXT,
ADD COLUMN IF NOT EXISTS content_clean_zh TEXT,
ADD COLUMN IF NOT EXISTS audio_url_zh TEXT,
ADD COLUMN IF NOT EXISTS audio_duration_ms_zh INTEGER;

-- Add Chinese label to topic_groups table
ALTER TABLE topic_groups
ADD COLUMN IF NOT EXISTS label_zh TEXT;

-- Add comments for clarity
COMMENT ON COLUMN segments.content_raw_zh IS 'Chinese translation of content_raw';
COMMENT ON COLUMN segments.content_clean_zh IS 'Chinese translation of content_clean (for TTS)';
COMMENT ON COLUMN segments.audio_url_zh IS 'URL to Chinese audio file in Cloud Storage';
COMMENT ON COLUMN segments.audio_duration_ms_zh IS 'Duration of Chinese audio in milliseconds';
COMMENT ON COLUMN topic_groups.label_zh IS 'Chinese translation of topic group label';
