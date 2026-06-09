-- Enable Row Level Security and scope anon (public browser key) access to
-- only what the frontend needs. The backend uses the service role key, which
-- bypasses RLS, so its full read/write access is unaffected.

ALTER TABLE issues       ENABLE ROW LEVEL SECURITY;
ALTER TABLE segments     ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks    ENABLE ROW LEVEL SECURITY;

-- Public (anon) read access — frontend fetches all four tables
CREATE POLICY "anon read issues"       ON issues       FOR SELECT TO anon USING (true);
CREATE POLICY "anon read segments"     ON segments     FOR SELECT TO anon USING (true);
CREATE POLICY "anon read topic_groups" ON topic_groups FOR SELECT TO anon USING (true);
CREATE POLICY "anon read bookmarks"    ON bookmarks    FOR SELECT TO anon USING (true);

-- Frontend creates bookmarks; allow anon insert only (no update/delete)
CREATE POLICY "anon insert bookmarks"  ON bookmarks    FOR INSERT TO anon WITH CHECK (true);

-- No anon UPDATE/DELETE policies => those operations are now blocked for the
-- public key, closing the destructive tamper/delete hole the advisor flagged.
