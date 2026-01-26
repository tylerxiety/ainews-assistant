-- Add audio fields to segments table for per-segment playback
ALTER TABLE segments 
ADD COLUMN IF NOT EXISTS audio_url TEXT,
ADD COLUMN IF NOT EXISTS audio_duration_ms INTEGER;

-- Add comment for clarity
COMMENT ON COLUMN segments.audio_url IS 'URL to the Cloud Storage hosted audio file for this specific segment.';
COMMENT ON COLUMN segments.audio_duration_ms IS 'Duration of the segment audio in milliseconds.';
