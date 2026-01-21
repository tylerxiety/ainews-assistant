import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { Issue, Segment, Bookmark } from '../types'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey)

/**
 * Fetch all issues, ordered by published date (newest first)
 */
export async function fetchIssues(): Promise<Issue[]> {
  const { data, error } = await supabase
    .from('issues')
    .select('*')
    .order('published_at', { ascending: false })

  if (error) throw error
  return data as Issue[]
}

/**
 * Fetch a single issue by ID
 */
export async function fetchIssue(issueId: string): Promise<Issue | null> {
  const { data, error } = await supabase
    .from('issues')
    .select('*')
    .eq('id', issueId)
    .single()

  if (error) throw error
  return data as Issue
}

/**
 * Fetch segments for an issue, ordered by order_index
 */
export async function fetchSegments(issueId: string): Promise<Segment[]> {
  const { data, error } = await supabase
    .from('segments')
    .select('*')
    .eq('issue_id', issueId)
    .order('order_index', { ascending: true })

  if (error) throw error
  return data as Segment[]
}

/**
 * Fetch issue with all its segments (legacy, flat list)
 */
export async function fetchIssueWithSegments(issueId: string): Promise<{ issue: Issue | null; segments: Segment[] }> {
  const [issue, segments] = await Promise.all([
    fetchIssue(issueId),
    fetchSegments(issueId),
  ])
  return { issue, segments }
}

/**
 * Fetch issue with topic groups and nested segments
 */
import { TopicGroup } from '../types'

export async function fetchIssueWithGroups(issueId: string): Promise<{ issue: Issue | null; groups: TopicGroup[] }> {
  const issuePromise = fetchIssue(issueId)

  const groupsPromise = supabase
    .from('topic_groups')
    .select('*, segments(*)')
    .eq('issue_id', issueId)
    .order('order_index', { ascending: true })

  const [issue, groupsResponse] = await Promise.all([issuePromise, groupsPromise])

  if (groupsResponse.error) throw groupsResponse.error

  const groups = groupsResponse.data as TopicGroup[]

  // Sort nested segments
  if (groups) {
    groups.forEach(g => {
      if (g.segments) {
        g.segments.sort((a, b) => a.order_index - b.order_index)
      }
    })
  }

  return { issue, groups }
}

/**
 * Fetch bookmarks for an issue
 */
export async function fetchBookmarks(issueId: string): Promise<Bookmark[]> {
  const { data, error } = await supabase
    .from('bookmarks')
    .select('*')
    .eq('issue_id', issueId)

  if (error) throw error
  return data as Bookmark[]
}

/**
 * Create a bookmark for a segment
 * @param {string} issueId - The issue UUID
 * @param {string} segmentId - The segment UUID
 * @param {string} clickupTaskId - The ClickUp task ID returned from API
 */
export async function createBookmark(issueId: string, segmentId: string, clickupTaskId: string): Promise<Bookmark> {
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
  return data as Bookmark
}
