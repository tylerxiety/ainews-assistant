import { useState, useEffect, useMemo, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { fetchIssues } from '../lib/supabase'
import { API_URL } from '../lib/api'
import { Issue } from '../types'
import { useLanguage } from '../i18n'
import { NEWSLETTER_SOURCES, getSourceInfo, ALL_SOURCES } from '../lib/sources'
import { useOfflineDownload } from '../hooks/useOfflineDownload'
import { Download, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import Loading from './Loading'
import './IssueList.css'

function DownloadButton({ issueId }: { issueId: string }) {
  const { t } = useLanguage()
  const { status, download } = useOfflineDownload(issueId)

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (status === 'idle' || status === 'error') {
      download()
    }
  }

  let icon
  let title: string
  switch (status) {
    case 'downloading':
      icon = <Loader2 size={18} className="spin" />
      title = t('issueList.downloading')
      break
    case 'done':
      icon = <CheckCircle2 size={18} />
      title = t('issueList.downloaded')
      break
    case 'error':
      icon = <AlertCircle size={18} />
      title = t('issueList.downloadError')
      break
    default:
      icon = <Download size={18} />
      title = t('issueList.download')
  }

  return (
    <button
      className={`download-btn ${status}`}
      onClick={handleClick}
      title={title}
      disabled={status === 'downloading'}
    >
      {icon}
    </button>
  )
}

type ProcessingStatus = 'idle' | 'processing' | 'done' | 'error'

export default function IssueList() {
  const { t } = useLanguage()
  const [issues, setIssues] = useState<Issue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeFilter, setActiveFilter] = useState<string>(
    () => sessionStorage.getItem('activeFilter') || ALL_SOURCES
  )

  const updateFilter = (filter: string) => {
    setActiveFilter(filter)
    sessionStorage.setItem('activeFilter', filter)
  }

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

  const filteredIssues = useMemo(() => {
    if (activeFilter === ALL_SOURCES) return issues
    return issues.filter(issue => (issue.source || 'ainews') === activeFilter)
  }, [issues, activeFilter])

  const sourceCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const issue of issues) {
      const src = issue.source || 'ainews'
      counts[src] = (counts[src] || 0) + 1
    }
    return counts
  }, [issues])

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

      <nav className="source-filters">
        <button
          className={`filter-tab ${activeFilter === ALL_SOURCES ? 'active' : ''}`}
          onClick={() => updateFilter(ALL_SOURCES)}
        >
          {t('issueList.allSources')} ({issues.length})
        </button>
        {Object.values(NEWSLETTER_SOURCES).map(src => (
          <button
            key={src.id}
            className={`filter-tab ${activeFilter === src.id ? 'active' : ''}`}
            onClick={() => updateFilter(src.id)}
          >
            {src.name} ({sourceCounts[src.id] || 0})
          </button>
        ))}
      </nav>

      {filteredIssues.length === 0 ? (
        <div className="empty">
          {issues.length === 0 ? (
            <>
              <p>{t('issueList.noIssues')}</p>
              <p className="hint">{t('issueList.noIssuesHint')}</p>
            </>
          ) : (
            <p>{t('issueList.noIssuesForSource', { source: getSourceInfo(activeFilter).name })}</p>
          )}
        </div>
      ) : (
        <ul>
          {filteredIssues.map((issue) => {
            const sourceInfo = getSourceInfo(issue.source)
            return (
              <li key={issue.id} className="issue-item">
                <Link to={`/player/${issue.id}`} className="issue-link">
                  <div className="issue-header">
                    <h2>{issue.title}</h2>
                    <span
                      className="source-badge"
                      style={{ backgroundColor: sourceInfo.color }}
                    >
                      {sourceInfo.name}
                    </span>
                  </div>
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
                {issue.processed_at && <DownloadButton issueId={issue.id} />}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
