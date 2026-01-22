import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchIssueWithGroups, fetchBookmarks, createBookmark } from '../lib/supabase'
import { isClickUpConfigured, createClickUpTask } from '../lib/clickup'
import { apiUrl } from '../lib/api'
import { Issue, Segment, TopicGroup, ConversationMessage } from '../types'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import Loading from './Loading'
import './Player.css'

const PLAYBACK_SPEEDS = [1, 1.25, 1.5, 2]

export default function Player() {
  const { issueId } = useParams<{ issueId: string }>()
  const [issue, setIssue] = useState<Issue | null>(null)
  const [groups, setGroups] = useState<TopicGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Q&A State
  const { isRecording, audioBlob, error: recorderError, startRecording, stopRecording } = useAudioRecorder()
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false)
  const [showQaPanel, setShowQaPanel] = useState(false)
  const [qaAudioUrl, setQaAudioUrl] = useState<string | null>(null)

  // Refs for Q&A
  const qaAudioRef = useRef<HTMLAudioElement | null>(null)
  const wasPlayingBeforeQa = useRef(false)
  const processedAudioRef = useRef<Blob | null>(null) // To prevent double submission

  // Bookmark state
  const [bookmarkedSegments, setBookmarkedSegments] = useState<Set<string>>(new Set())
  const [bookmarkingSegment, setBookmarkingSegment] = useState<string | null>(null) // ID of segment being bookmarked
  const [bookmarkError, setBookmarkError] = useState<string | null>(null)

  // Audio state
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const shouldAutoPlayRef = useRef(false)
  const groupRefs = useRef<(HTMLDivElement | null)[]>([])
  const hasInteractedRef = useRef(false) // Track if user has interacted (to skip initial scroll)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

  // Q&A Effects

  // Handle audio recording completion
  useEffect(() => {
    // If we stopped recording and have an audio blob, send it
    if (!isRecording && audioBlob && audioBlob !== processedAudioRef.current && !recorderError) {
      handleAskQuestionWithAudio(audioBlob)
      processedAudioRef.current = audioBlob
    }
  }, [isRecording, audioBlob, recorderError])

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      // Pause main audio if playing
      if (isPlaying) {
        wasPlayingBeforeQa.current = true
        handlePause()
      } else {
        wasPlayingBeforeQa.current = false
      }

      processedAudioRef.current = null
      setShowQaPanel(true)
      startRecording()
    }
  }

  const handleAskQuestionWithAudio = async (audioBlob: Blob) => {
    if (!issueId || !groups[currentGroupIndex]) return

    // Add user message (placeholder while transcribing)
    const userMsg: ConversationMessage = {
      role: 'user',
      text: 'Transcribing...',
      timestamp: Date.now()
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoadingAnswer(true)

    try {
      // Prepare FormData
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('issue_id', issueId)
      formData.append('group_id', groups[currentGroupIndex].id)

      // Call backend
      const response = await fetch(apiUrl('/ask-audio'), {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to get answer')
      }

      const data = await response.json()

      // Update user message with transcription
      setMessages(prev =>
        prev.map((msg, idx) =>
          idx === prev.length - 1 ? { ...msg, text: data.transcript || msg.text } : msg
        )
      )

      // Add assistant message
      const assistantMsg: ConversationMessage = {
        role: 'assistant',
        text: data.answer,
        audioUrl: data.audio_url,
        timestamp: Date.now()
      }
      setMessages(prev => [...prev, assistantMsg])

      // Play response audio
      if (data.audio_url) {
        setQaAudioUrl(data.audio_url)
      } else {
        // If no audio, resume main audio after a delay
        setTimeout(() => {
          if (wasPlayingBeforeQa.current) {
            handlePlay()
          }
        }, 2000)
      }

    } catch (err) {
      if (import.meta.env.DEV) {
        console.error('Q&A Error:', err)
      }
      const errorMsg: ConversationMessage = {
        role: 'assistant',
        text: "Sorry, I couldn't get an answer at this time.",
        timestamp: Date.now()
      }
      setMessages(prev => [...prev, errorMsg])
      setIsLoadingAnswer(false)

      // Resume main audio
      if (wasPlayingBeforeQa.current) {
        handlePlay()
      }
    } finally {
      setIsLoadingAnswer(false)
    }
  }

  // Play QA audio when URL changes
  useEffect(() => {
    if (qaAudioUrl && qaAudioRef.current) {
      qaAudioRef.current.src = qaAudioUrl
      qaAudioRef.current.play().catch(e => {
        if (import.meta.env.DEV) {
          console.error("QA Playback failed:", e)
        }
      })
    }
  }, [qaAudioUrl])

  const handleQaEnded = () => {
    setQaAudioUrl(null)
    if (wasPlayingBeforeQa.current) {
      handlePlay()
    }
  }

  // Load issue, groups, and bookmarks
  useEffect(() => {
    async function loadData() {
      if (!issueId) return

      try {
        const { issue, groups } = await fetchIssueWithGroups(issueId)
        setIssue(issue)
        // Only groups with audio
        setGroups(groups.filter((g) => g.audio_url))

        // Load existing bookmarks
        try {
          const bookmarks = await fetchBookmarks(issueId)
          const bookmarkedIds = new Set(bookmarks.map(b => b.segment_id))
          setBookmarkedSegments(bookmarkedIds)
        } catch (err) {
          // Bookmarks table might not exist yet, silently ignore
          // In development, log for debugging

        }
      } catch (err: any) {
        setError(err.message || 'Unknown error')
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [issueId])

  // Set audio source when current group changes
  useEffect(() => {
    if (audioRef.current && groups[currentGroupIndex]?.audio_url) {
      const audio = audioRef.current

      // Reset time display while loading
      setCurrentTime(0)
      setDuration(0)

      // Set up handler to play once audio is ready
      const handleCanPlay = () => {
        if (shouldAutoPlayRef.current) {
          audio.play().catch((e) => {
            if (import.meta.env.DEV) {
              console.log("Autoplay prevented:", e)
            }
          })
        }
        audio.removeEventListener('canplay', handleCanPlay)
      }

      audio.addEventListener('canplay', handleCanPlay)
      audio.src = groups[currentGroupIndex].audio_url || ''
      audio.load()

      return () => {
        audio.removeEventListener('canplay', handleCanPlay)
      }
    }
  }, [currentGroupIndex, groups, loading])

  // Update playback rate when speed changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  // Clear refs when groups change
  useEffect(() => {
    groupRefs.current = groupRefs.current.slice(0, groups.length)
  }, [groups])

  // Auto-scroll to current group (only after user interaction)
  useEffect(() => {
    if (!hasInteractedRef.current) return

    const currentRef = groupRefs.current[currentGroupIndex]
    if (currentRef) {
      currentRef.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }
  }, [currentGroupIndex])

  const handleAudioError = (e: React.SyntheticEvent<HTMLAudioElement, Event>) => {
    const target = e.target as HTMLAudioElement
    setError(`Audio playback failed: ${target.error?.message || 'Unknown error'}`)
    setIsPlaying(false)
  }

  const handlePlay = () => {
    if (audioRef.current) {
      hasInteractedRef.current = true
      shouldAutoPlayRef.current = true
      const playPromise = audioRef.current.play()

      if (playPromise !== undefined) {
        playPromise.catch(err => {
          if (import.meta.env.DEV) {
            console.error("Play failed:", err)
          }
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
    // Move to next group
    if (currentGroupIndex < groups.length - 1) {
      shouldAutoPlayRef.current = true
      setCurrentGroupIndex(currentGroupIndex + 1)
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

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (audioRef.current && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      audioRef.current.currentTime = percentage * duration
    }
  }

  const handleGroupClick = (index: number) => {
    hasInteractedRef.current = true
    setCurrentGroupIndex(index)
    if (!isPlaying) {
      handlePlay()
    }
  }

  const cyclePlaybackSpeed = () => {
    const currentIndex = PLAYBACK_SPEEDS.indexOf(playbackSpeed)
    const nextIndex = (currentIndex + 1) % PLAYBACK_SPEEDS.length
    setPlaybackSpeed(PLAYBACK_SPEEDS[nextIndex])
  }

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Handle bookmark click
  const handleBookmark = async (e: React.MouseEvent, segment: Segment) => {
    e.stopPropagation() // Don't trigger group click

    if (!issueId || !issue) return

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
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.error('Bookmark failed:', err)
      }
      setBookmarkError(err.message || 'Unknown error')
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

      {/* QA Audio element (hidden) */}
      <audio
        ref={qaAudioRef}
        onEnded={handleQaEnded}
      />

      {/* Audio controls */}
      <div className="audio-controls">
        <button
          className="play-pause-btn"
          onClick={handlePlayPause}
          disabled={groups.length === 0}
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

        <button
          className={`mic-btn ${isRecording ? 'listening' : ''}`}
          onClick={handleMicClick}
          title="Ask a question about this section"
        >
          {isRecording ? '🔴' : '🎤'}
        </button>

        <span className="segment-indicator">
          {groups.length > 0 ? `${currentGroupIndex + 1}/${groups.length}` : '0/0'}
        </span>
      </div>

      {/* QA Panel */}
      {showQaPanel && (
        <div className="qa-panel">
          <div className="qa-header">
            <h3>Q&A</h3>
            <button className="close-qa" onClick={() => setShowQaPanel(false)}>×</button>
          </div>
          <div className="qa-messages">
            {messages.length === 0 && !isRecording && (
              <p className="qa-placeholder">Tap the mic to ask a question about this section.</p>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`qa-message ${msg.role}`}>
                <p>{msg.text}</p>
              </div>
            ))}
            {isRecording && (
              <div className="qa-message user listening">
                <p>Recording...</p>
              </div>
            )}
            {isLoadingAnswer && (
              <div className="qa-message assistant loading">
                <p>Thinking...</p>
              </div>
            )}
            {recorderError && (
              <div className="qa-message error">
                <p>Error: {recorderError}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Topic Groups List */}
      <div className="segments-list">
        {groups.length === 0 ? (
          <p className="no-segments">No audio segments available.</p>
        ) : (
          groups.map((group, index) => (
            <div
              key={group.id}
              ref={(el) => { groupRefs.current[index] = el }}
              className={`segment topic-group ${index === currentGroupIndex ? 'active' : ''}`}
              onClick={() => handleGroupClick(index)}
            >
              <div className="group-content">
                {group.label && <h3 className="group-title">{group.label}</h3>}

                <div className="group-items">
                  {group.segments.map((segment) => (
                    <div key={segment.id} className="group-item">
                      <p>{segment.content_raw}</p>

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

                      {/* Bookmark button */}
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
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
