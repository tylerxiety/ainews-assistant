-- Newsletter Audio Player - Initial Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Newsletter issues
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  url TEXT UNIQUE NOT NULL,
  published_at TIMESTAMPTZ,
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual items (per-item audio for fine-grained sync)
CREATE TABLE segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
  segment_type TEXT NOT NULL, -- 'section_header' | 'item'
  content_raw TEXT NOT NULL,  -- Original text with links
  content_clean TEXT NOT NULL, -- Cleaned for TTS
  links JSONB DEFAULT '[]',   -- [{text, url}] for tap-to-open
  audio_url TEXT,             -- GCS URL
  audio_duration_ms INTEGER,
  order_index INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookmarks saved to ClickUp
CREATE TABLE bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id UUID REFERENCES segments(id) ON DELETE CASCADE,
  clickup_task_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_segments_issue_id ON segments(issue_id);
CREATE INDEX idx_segments_order ON segments(issue_id, order_index);
CREATE INDEX idx_bookmarks_segment_id ON bookmarks(segment_id);

-- Comments
COMMENT ON TABLE issues IS 'Newsletter issues from RSS feed';
COMMENT ON TABLE segments IS 'Individual segments of newsletter content with audio';
COMMENT ON TABLE bookmarks IS 'User bookmarks synced to ClickUp';
COMMENT ON COLUMN segments.segment_type IS 'Type: section_header or item';
COMMENT ON COLUMN segments.links IS 'JSON array of link objects: [{text, url}]';
