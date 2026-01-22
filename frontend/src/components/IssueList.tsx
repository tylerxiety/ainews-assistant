import { useState, useEffect, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { fetchIssues } from '../lib/supabase'
import { API_URL } from '../lib/api'
import { Issue } from '../types'
import Loading from './Loading'
import './IssueList.css'

type ProcessingStatus = 'idle' | 'processing' | 'done' | 'error'

export default function IssueList() {
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Processing state
  const [url, setUrl] = useState('')
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>('idle')
  const [processError, setProcessError] = useState<string | null>(null)

  const loadIssues = async () => {
    try {
      const data = await fetchIssues()
      setIssues(data)
    } catch (err: any) {
      setError(err.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadIssues()
  }, [])

  const handleProcess = async (e: FormEvent) => {
    e.preventDefault()
    if (!url) return

    setProcessingStatus('processing')
    setProcessError(null)

    try {
      const response = await fetch(`${API_URL}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      await response.json()

      setProcessingStatus('done')
      setUrl('')
      // Give backend a moment to start processing task
      setTimeout(() => {
        loadIssues()
      }, 1000)
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.error('Processing failed:', err)
      }
      setProcessingStatus('error')
      setProcessError(err.message || 'Failed to start processing')
    }
  }

  if (loading) {
    return <Loading message="Loading newsletters..." />
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">!</div>
        <p className="error-message">Failed to load newsletters</p>
        <p className="error-detail">{error}</p>
        <button className="retry-btn" onClick={() => window.location.reload()}>
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="issue-list">
      <header className="issue-list-header">
        <h1>Newsletter Issues</h1>
        <Link to="/settings" className="settings-link" title="Settings">⚙️</Link>
      </header>

      <section className="process-section">
        <form onSubmit={handleProcess} className="process-form">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste newsletter URL..."
            required
            disabled={processingStatus === 'processing'}
            className="url-input"
          />
          <button
            type="submit"
            disabled={processingStatus === 'processing' || !url}
            className="process-btn"
          >
            {processingStatus === 'processing' ? 'Processing...' : 'Add'}
          </button>
        </form>
        {processingStatus === 'error' && (
          <div className="process-error">{processError}</div>
        )}
        {processingStatus === 'done' && (
          <div className="process-success">Processing started! It will appear below shortly.</div>
        )}
      </section>

      {issues.length === 0 ? (
        <div className="empty">
          <p>No issues found.</p>
          <p className="hint">Process a newsletter above to get started.</p>
        </div>
      ) : (
        <ul>
          {issues.map((issue) => (
            <li key={issue.id} className="issue-item">
              <Link to={`/player/${issue.id}`}>
                <h2>{issue.title}</h2>
                <div className="issue-meta">
                  <span className="published-date">
                    {issue.published_at
                      ? new Date(issue.published_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })
                      : 'Unknown date'}
                  </span>
                  <span className={`status ${issue.processed_at ? 'processed' : 'pending'}`}>
                    {issue.processed_at ? 'Ready to play' : 'Processing...'}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
