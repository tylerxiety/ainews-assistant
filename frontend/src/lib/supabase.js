import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

/**
 * Fetch all issues, ordered by published date (newest first)
 */
export async function fetchIssues() {
  const { data, error } = await supabase
    .from('issues')
    .select('*')
    .order('published_at', { ascending: false })

  if (error) throw error
  return data
}

/**
 * Fetch a single issue by ID
 */
export async function fetchIssue(issueId) {
  const { data, error } = await supabase
    .from('issues')
    .select('*')
    .eq('id', issueId)
    .single()

  if (error) throw error
  return data
}

/**
 * Fetch segments for an issue, ordered by order_index
 */
export async function fetchSegments(issueId) {
  const { data, error } = await supabase
    .from('segments')
    .select('*')
    .eq('issue_id', issueId)
    .order('order_index', { ascending: true })

  if (error) throw error
  return data
}

/**
 * Fetch issue with all its segments
 */
export async function fetchIssueWithSegments(issueId) {
  const [issue, segments] = await Promise.all([
    fetchIssue(issueId),
    fetchSegments(issueId),
  ])
  return { issue, segments }
}

/**
 * Fetch bookmarks for an issue
 */
export async function fetchBookmarks(issueId) {
  const { data, error } = await supabase
    .from('bookmarks')
    .select('*')
    .eq('issue_id', issueId)

  if (error) throw error
  return data
}

/**
 * Create a bookmark for a segment
 * @param {string} issueId - The issue UUID
 * @param {string} segmentId - The segment UUID
 * @param {string} clickupTaskId - The ClickUp task ID returned from API
 */
export async function createBookmark(issueId, segmentId, clickupTaskId) {
  const { data, error } = await supabase
    .from('bookmarks')
    .insert({
      issue_id: issueId,
      segment_id: segmentId,
      clickup_task_id: clickupTaskId,
    })
    .select()
    .single()

  if (error) throw error
  return data
}
