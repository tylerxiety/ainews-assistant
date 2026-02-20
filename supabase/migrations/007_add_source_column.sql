ALTER TABLE issues ADD COLUMN source TEXT;
CREATE INDEX idx_issues_source ON issues(source);
