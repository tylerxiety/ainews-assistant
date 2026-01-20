import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchIssueWithSegments, fetchBookmarks, createBookmark } from '../lib/supabase'
import { isClickUpConfigured, createClickUpTask } from '../lib/clickup'
import Loading from './Loading'
import './Player.css'

const PLAYBACK_SPEEDS = [1, 1.25, 1.5, 2]

export default function Player() {
  const { issueId } = useParams()
  const [issue, setIssue] = useState(null)
  const [segments, setSegments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Bookmark state
  const [bookmarkedSegments, setBookmarkedSegments] = useState(new Set())
  const [bookmarkingSegment, setBookmarkingSegment] = useState(null) // ID of segment being bookmarked
  const [bookmarkError, setBookmarkError] = useState(null)

  // Audio state
  const audioRef = useRef(null)
  const shouldAutoPlayRef = useRef(false)
  const segmentRefs = useRef([])
  const hasInteractedRef = useRef(false) // Track if user has interacted (to skip initial scroll)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  // Load issue, segments, and bookmarks
  useEffect(() => {
    async function loadData() {
      try {
        const { issue, segments } = await fetchIssueWithSegments(issueId)
        setIssue(issue)
        setSegments(segments.filter((s) => s.audio_url)) // Only segments with audio

        // Load existing bookmarks
        try {
          const bookmarks = await fetchBookmarks(issueId)
          const bookmarkedIds = new Set(bookmarks.map(b => b.segment_id))
          setBookmarkedSegments(bookmarkedIds)
        } catch (err) {
          // Bookmarks table might not exist yet, silently ignore
          // In development, log for debugging

        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [issueId])

  // Set audio source when current segment changes
  useEffect(() => {
    if (audioRef.current && segments[currentSegmentIndex]?.audio_url) {
      const audio = audioRef.current

      // Reset time display while loading
      setCurrentTime(0)
      setDuration(0)

      // Set up handler to play once audio is ready
      const handleCanPlay = () => {
        if (shouldAutoPlayRef.current) {
          audio.play().catch(() => { })
        }
        audio.removeEventListener('canplay', handleCanPlay)
      }

      audio.addEventListener('canplay', handleCanPlay)
      audio.src = segments[currentSegmentIndex].audio_url
      audio.load()

      return () => {
        audio.removeEventListener('canplay', handleCanPlay)
      }
    }
  }, [currentSegmentIndex, segments, loading])

  // Update playback rate when speed changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  // Clear refs when segments change to prevent memory leaks
  useEffect(() => {
    segmentRefs.current = segmentRefs.current.slice(0, segments.length)
  }, [segments])

  // Auto-scroll to current segment (only after user interaction)
  useEffect(() => {
    if (!hasInteractedRef.current) return

    const currentRef = segmentRefs.current[currentSegmentIndex]
    if (currentRef) {
      currentRef.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }, [currentSegmentIndex])

  const handleAudioError = (e) => {

    setError(`Audio playback failed: ${e.target.error?.message || 'Unknown error'}`)
    setIsPlaying(false)
  }

  const handlePlay = () => {
    if (audioRef.current) {
      hasInteractedRef.current = true
      shouldAutoPlayRef.current = true
      const playPromise = audioRef.current.play()

      if (playPromise !== undefined) {
        playPromise.catch(err => {
          console.error("Play failed:", err)
          // Don't show error for aborts (user clicked pause/next quickly)
          if (err.name !== 'AbortError') {
            setError(`Playback failed: ${err.message}`)
          }
          setIsPlaying(false)
        })
      }
      setIsPlaying(true)
    }
  }

  const handlePause = () => {
    if (audioRef.current) {
      shouldAutoPlayRef.current = false
      audioRef.current.pause()
      setIsPlaying(false)
    }
  }

  const handlePlayPause = () => {
    if (isPlaying) {
      handlePause()
    } else {
      handlePlay()
    }
  }

  const handleEnded = () => {
    // Move to next segment
    if (currentSegmentIndex < segments.length - 1) {
      // Keep autoplay enabled for continuous playback
      shouldAutoPlayRef.current = true
      setCurrentSegmentIndex(currentSegmentIndex + 1)
    } else {
      shouldAutoPlayRef.current = false
      setIsPlaying(false)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleProgressClick = (e) => {
    if (audioRef.current && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      audioRef.current.currentTime = percentage * duration
    }
  }

  const handleSegmentClick = (index) => {
    hasInteractedRef.current = true
    setCurrentSegmentIndex(index)
    if (!isPlaying) {
      handlePlay()
    }
  }

  const cyclePlaybackSpeed = () => {
    const currentIndex = PLAYBACK_SPEEDS.indexOf(playbackSpeed)
    const nextIndex = (currentIndex + 1) % PLAYBACK_SPEEDS.length
    setPlaybackSpeed(PLAYBACK_SPEEDS[nextIndex])
  }

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Handle bookmark click
  const handleBookmark = async (e, segment) => {
    e.stopPropagation() // Don't trigger segment click

    // Check if already bookmarked
    if (bookmarkedSegments.has(segment.id)) {
      return
    }

    // Check if ClickUp is configured
    if (!isClickUpConfigured()) {
      setBookmarkError('ClickUp not configured. Go to Settings to set up your API token.')
      setTimeout(() => setBookmarkError(null), 4000)
      return
    }

    setBookmarkingSegment(segment.id)
    setBookmarkError(null)

    try {
      // Create task in ClickUp
      const clickupTask = await createClickUpTask(segment, issue.title)

      // Save bookmark to Supabase
      await createBookmark(issueId, segment.id, clickupTask.id)

      // Update local state
      setBookmarkedSegments(prev => new Set([...prev, segment.id]))
    } catch (err) {
      // Log error in development only
      if (import.meta.env.DEV) {
        console.error('Bookmark failed:', err)
      }
      setBookmarkError(err.message)
      setTimeout(() => setBookmarkError(null), 4000)
    } finally {
      setBookmarkingSegment(null)
    }
  }

  if (loading) {
    return <Loading message="Loading newsletter..." />
  }

  if (error) {
    return (
      <div className="player-error">
        <Link to="/" className="back-link">&larr; Back</Link>
        <div className="error-container">
          <div className="error-icon">!</div>
          <p className="error-message">Failed to load newsletter</p>
          <p className="error-detail">{error}</p>
          <button className="retry-btn" onClick={() => window.location.reload()}>
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!issue) {
    return (
      <div className="player-error">
        <Link to="/" className="back-link">&larr; Back</Link>
        <div className="error-container">
          <div className="error-icon">?</div>
          <p className="error-message">Newsletter not found</p>
          <Link to="/" className="retry-btn">Go back home</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="player">
      <header className="player-header">
        <div className="header-nav">
          <Link to="/" className="back-link">&larr; Back</Link>
          <Link to="/settings" className="settings-link" title="Settings">⚙️</Link>
        </div>
        <h1>{issue.title}</h1>
        {issue.published_at && (
          <p className="published-date">
            {new Date(issue.published_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        )}
      </header>

      {/* Bookmark error toast */}
      {bookmarkError && (
        <div className="bookmark-error-toast">
          <span className="toast-icon">⚠️</span>
          <span>{bookmarkError}</span>
        </div>
      )}

      {/* Audio element (hidden) */}
      <audio
        ref={audioRef}
        onEnded={handleEnded}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={handleAudioError}
      />

      {/* Audio controls */}
      <div className="audio-controls">
        <button
          className="play-pause-btn"
          onClick={handlePlayPause}
          disabled={segments.length === 0}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <div className="progress-container" onClick={handleProgressClick}>
          <div
            className="progress-bar"
            style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
          />
        </div>

        <span className="time-display">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <button className="speed-btn" onClick={cyclePlaybackSpeed}>
          {playbackSpeed}x
        </button>

        <span className="segment-indicator">
          {segments.length > 0 ? `${currentSegmentIndex + 1}/${segments.length}` : '0/0'}
        </span>
      </div>

      {/* Segments list */}
      <div className="segments-list">
        {segments.length === 0 ? (
          <p className="no-segments">No audio segments available.</p>
        ) : (
          segments.map((segment, index) => (
            <div
              key={segment.id}
              ref={(el) => (segmentRefs.current[index] = el)}
              className={`segment ${index === currentSegmentIndex ? 'active' : ''} ${segment.segment_type === 'section_header' ? 'header' : 'item'
                }`}
              onClick={() => handleSegmentClick(index)}
            >
              <div className="segment-content">
                {segment.segment_type === 'section_header' ? (
                  <h3>{segment.content_raw}</h3>
                ) : (
                  <p>{segment.content_raw}</p>
                )}
                {segment.links && segment.links.length > 0 && (
                  <div className="segment-links">
                    {segment.links.map((link, i) => (
                      <a
                        key={i}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {link.text || 'Link'}
                      </a>
                    ))}
                  </div>
                )}
              </div>

              {/* Bookmark button - only show for items, not headers */}
              {segment.segment_type !== 'section_header' && (
                <button
                  className={`bookmark-btn ${bookmarkedSegments.has(segment.id) ? 'bookmarked' : ''}`}
                  onClick={(e) => handleBookmark(e, segment)}
                  disabled={bookmarkingSegment === segment.id || bookmarkedSegments.has(segment.id)}
                  title={bookmarkedSegments.has(segment.id) ? 'Bookmarked to ClickUp' : 'Bookmark to ClickUp'}
                >
                  {bookmarkingSegment === segment.id ? (
                    <span className="bookmark-loading">⏳</span>
                  ) : bookmarkedSegments.has(segment.id) ? (
                    <span className="bookmark-done">✓</span>
                  ) : (
                    <span className="bookmark-icon">📌</span>
                  )}
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
