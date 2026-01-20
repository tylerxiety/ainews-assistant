import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchIssues } from '../lib/supabase'
import Loading from './Loading'
import './IssueList.css'

export default function IssueList() {
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadIssues() {
      try {
        const data = await fetchIssues()
        setIssues(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadIssues()
  }, [])

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

  if (issues.length === 0) {
    return (
      <div className="empty">
        <p>No issues found.</p>
        <p className="hint">Process a newsletter using the backend API to get started.</p>
      </div>
    )
  }

  return (
    <div className="issue-list">
      <header className="issue-list-header">
        <h1>Newsletter Issues</h1>
        <Link to="/settings" className="settings-link" title="Settings">⚙️</Link>
      </header>
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
    </div>
  )
}
