import { useState, useEffect, useCallback } from 'react'
import { fetchIssueWithGroups } from '../lib/supabase'

type DownloadStatus = 'idle' | 'downloading' | 'done' | 'error'

const STORAGE_KEY = 'offline-downloads'

function isDownloaded(issueId: string): boolean {
  try {
    const ids: string[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return ids.includes(issueId)
  } catch {
    return false
  }
}

function markDownloaded(issueId: string) {
  try {
    const ids: string[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    if (!ids.includes(issueId)) {
      ids.push(issueId)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
    }
  } catch { /* ignore */ }
}

export function useOfflineDownload(issueId: string) {
  const [status, setStatus] = useState<DownloadStatus>(() =>
    isDownloaded(issueId) ? 'done' : 'idle'
  )

  // Sync if localStorage changes (e.g. another tab)
  useEffect(() => {
    setStatus(isDownloaded(issueId) ? 'done' : 'idle')
  }, [issueId])

  const download = useCallback(async () => {
    setStatus('downloading')
    try {
      // Pre-fetch issue data — SW caches the Supabase responses via NetworkFirst
      await fetchIssueWithGroups(issueId)
      markDownloaded(issueId)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }, [issueId])

  return { status, download }
}
