-- Add issue_id to bookmarks table for easier querying
ALTER TABLE bookmarks 
ADD COLUMN issue_id UUID REFERENCES issues(id) ON DELETE CASCADE;

-- Create index for performance
CREATE INDEX idx_bookmarks_issue_id ON bookmarks(issue_id);
