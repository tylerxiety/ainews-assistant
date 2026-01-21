-- Create topic_groups table
CREATE TABLE IF NOT EXISTS topic_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID REFERENCES issues(id) ON DELETE CASCADE,
    label TEXT, -- The topic title
    audio_url TEXT,
    audio_duration_ms INTEGER,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add topic_group_id to segments
ALTER TABLE segments ADD COLUMN IF NOT EXISTS topic_group_id UUID REFERENCES topic_groups(id) ON DELETE SET NULL;

-- Indexes
CREATE INDEX idx_topic_groups_issue_id ON topic_groups(issue_id);
CREATE INDEX idx_segments_topic_group_id ON segments(topic_group_id);

COMMENT ON TABLE topic_groups IS 'Groups of segments (title + items) played as one audio unit';
