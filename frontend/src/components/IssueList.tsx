import { useState, useEffect, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { fetchIssues } from '../lib/supabase'
import { API_URL } from '../lib/api'
import { Issue } from '../types'
import { useLanguage } from '../i18n'
import Loading from './Loading'
import './IssueList.css'

type ProcessingStatus = 'idle' | 'processing' | 'done' | 'error'

export default function IssueList() {
  const { t } = useLanguage()
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start processing'
      if (import.meta.env.DEV) {
        console.error('Processing failed:', message)
      }
      setProcessingStatus('error')
      setProcessError(message)
    }
  }

  if (loading) {
    return <Loading />
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">!</div>
        <p className="error-message">{t('issueList.loadFailed')}</p>
        <p className="error-detail">{error}</p>
        <button className="retry-btn" onClick={() => window.location.reload()}>
          {t('common.tryAgain')}
        </button>
      </div>
    )
  }

  return (
    <div className="issue-list">
      <header className="issue-list-header">
        <h1>{t('issueList.title')}</h1>
        <Link to="/settings" className="settings-link" title={t('common.settings')}>⚙️</Link>
      </header>

      <section className="process-section">
        <form onSubmit={handleProcess} className="process-form">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={t('issueList.urlPlaceholder')}
            required
            disabled={processingStatus === 'processing'}
            className="url-input"
          />
          <button
            type="submit"
            disabled={processingStatus === 'processing' || !url}
            className="process-btn"
          >
            {processingStatus === 'processing' ? t('issueList.processing') : t('common.add')}
          </button>
        </form>
        {processingStatus === 'error' && (
          <div className="process-error">{processError}</div>
        )}
        {processingStatus === 'done' && (
          <div className="process-success">{t('issueList.processSuccess')}</div>
        )}
      </section>

      {issues.length === 0 ? (
        <div className="empty">
          <p>{t('issueList.noIssues')}</p>
          <p className="hint">{t('issueList.noIssuesHint')}</p>
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
                      ? new Date(issue.published_at).toLocaleDateString(t('dates.locale'), {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })
                      : t('common.unknownDate')}
                  </span>
                  <span className={`status ${issue.processed_at ? 'processed' : 'pending'}`}>
                    {issue.processed_at ? t('issueList.readyToPlay') : t('issueList.processing')}
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
