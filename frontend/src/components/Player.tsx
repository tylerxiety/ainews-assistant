import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchIssueWithGroups, fetchBookmarks, createBookmark } from '../lib/supabase'
import { isClickUpConfigured, createClickUpTask } from '../lib/clickup'
import { apiUrl } from '../lib/api'
import { Issue, Segment, TopicGroup, ConversationMessage } from '../types'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import { useVoiceMode } from '../hooks/useVoiceMode'
import { usePlaybackState } from '../hooks/usePlaybackState'
import { useLanguage } from '../i18n'
import Loading from './Loading'
import { CONFIG } from '../config'
import './Player.css'

import AudioBar from './AudioBar'
import SegmentList from './SegmentList'
import SidePanel from './SidePanel'

const PLAYBACK_SPEEDS = [1, 1.25, 1.5, 2]

export default function Player() {
  const { t, language } = useLanguage()
  const { issueId } = useParams<{ issueId: string }>()
  const [issue, setIssue] = useState<Issue | null>(null)
  const [groups, setGroups] = useState<TopicGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Q&A State
  const { isRecording, audioBlob, error: recorderError, startRecording, stopRecording } = useAudioRecorder()
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [isLoadingAnswer, setIsLoadingAnswer] = useState(false)
  // Replaced showQaPanel with sidePanel state
  const [sidePanelOpen, setSidePanelOpen] = useState(false)
  const [sidePanelTab, setSidePanelTab] = useState<'toc' | 'qa'>('toc')

  const [qaAudioUrl, setQaAudioUrl] = useState<string | null>(null)
  const [isPlayingQaAudio, setIsPlayingQaAudio] = useState(false)
  const [qaPlaybackFailed, setQaPlaybackFailed] = useState(false)
  const [isResumingNewsletter, setIsResumingNewsletter] = useState(false)
  const [voiceError, setVoiceError] = useState<string | null>(null)

  // Refs for Q&A
  const savedNewsletterPositionRef = useRef<number>(0)
  const savedNewsletterDurationRef = useRef<number>(0)
  const savedNewsletterSrcRef = useRef<string | null>(null)
  const wasPlayingBeforeQa = useRef(false)
  const isPlayingQaAudioRef = useRef(false)
  const isResumingNewsletterRef = useRef(false)
  const processedAudioRef = useRef<Blob | null>(null) // To prevent double submission
  const wasPlayingBeforeVoiceRef = useRef(false)
  const pendingVoiceQuestionRef = useRef(false)
  const voiceQuestionIndexRef = useRef<number | null>(null)
  const voiceAnswerIndexRef = useRef<number | null>(null)
  const voiceAnswerTextRef = useRef('')

  // Bookmark state
  const [bookmarkedSegments, setBookmarkedSegments] = useState<Set<string>>(new Set())
  const [bookmarkingSegment, setBookmarkingSegment] = useState<string | null>(null) // ID of segment being bookmarked
  const [bookmarkError, setBookmarkError] = useState<string | null>(null)

  // Audio state
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const shouldAutoPlayRef = useRef(false)
  const hasInteractedRef = useRef(false) // Track if user has interacted (to skip initial scroll)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentGroupIndex, setCurrentGroupIndex] = useState(0)
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const currentGroupIndexRef = useRef(currentGroupIndex)
  const currentSegmentIndexRef = useRef(currentSegmentIndex)
  const prevLanguageRef = useRef(language)

  // Playback State Persistence
  const { restoredState, clearState } = usePlaybackState(issueId, currentGroupIndex, currentSegmentIndex)

  useEffect(() => {
    currentGroupIndexRef.current = currentGroupIndex
    currentSegmentIndexRef.current = currentSegmentIndex
  }, [currentGroupIndex, currentSegmentIndex])

  // Handle audio recording completion
  useEffect(() => {
    // If we stopped recording and have an audio blob, send it
    if (!isRecording && audioBlob && audioBlob !== processedAudioRef.current && !recorderError) {
      handleAskQuestionWithAudio(audioBlob)
      processedAudioRef.current = audioBlob
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- handleAskQuestionWithAudio intentionally omitted; processedAudioRef prevents double-fire
  }, [isRecording, audioBlob, recorderError])

  const handleMicClick = () => {
    if (isVoiceModeActive) {
      handleVoiceError(t('player.voiceModeConflict'))
      return
    }
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

      // Open panel to QA
      setSidePanelOpen(true)
      setSidePanelTab('qa')

      startRecording()
    }
  }

  const handleVoiceError = (message: string) => {
    setVoiceError(message)
    setTimeout(() => setVoiceError(null), 4000)
  }

  const mergeTranscriptText = (current: string, incoming: string) => {
    const trimmed = incoming.trim()
    if (!trimmed) return current
    if (!current) return trimmed
    if (trimmed.startsWith(current)) return trimmed
    if (current.endsWith(trimmed)) return current

    const maxOverlap = Math.min(current.length, trimmed.length)
    for (let i = maxOverlap; i > 0; i -= 1) {
      if (current.slice(-i) === trimmed.slice(0, i)) {
        return `${current}${trimmed.slice(i)}`.trim()
      }
    }

    return `${current} ${trimmed}`.trim()
  }

  const addVoiceQuestionMessage = () => {
    setMessages(prev => {
      voiceQuestionIndexRef.current = prev.length
      return [
        ...prev,
        {
          role: 'user',
          text: '[user question]',
          timestamp: Date.now(),
        },
      ]
    })
  }

  const updateVoiceAnswerMessage = (text: string) => {
    setMessages(prev => {
      if (voiceAnswerIndexRef.current === null) {
        voiceAnswerIndexRef.current = prev.length
        return [
          ...prev,
          {
            role: 'assistant',
            text,
            timestamp: Date.now(),
          },
        ]
      }

      return prev.map((msg, idx) =>
        idx === voiceAnswerIndexRef.current ? { ...msg, text } : msg
      )
    })
  }

  const pauseNewsletterForVoice = (captureWasPlaying = false) => {
    const audio = audioRef.current
    if (!audio) {
      if (captureWasPlaying) {
        wasPlayingBeforeVoiceRef.current = false
      }
      return
    }

    if (captureWasPlaying) {
      wasPlayingBeforeVoiceRef.current = !audio.paused
    }

    if (!audio.paused) {
      shouldAutoPlayRef.current = false
      audio.pause()
      setIsPlaying(false)
      return
    }
  }

  const resumeNewsletterAfterVoice = (delayMs = 0) => {
    if (wasPlayingBeforeVoiceRef.current) {
      window.setTimeout(() => {
        handlePlay()
      }, delayMs)
    }
  }

  // Helper to check if segment has audio for current language
  const segmentHasAudio = useCallback((seg: Segment) => {
    if (language === 'zh') return !!seg.audio_url_zh
    return !!seg.audio_url
  }, [language])

  // Helper to check if group (section header) has audio for current language
  const groupHasAudio = useCallback((group: TopicGroup) => {
    if (language === 'zh') return !!group.audio_url_zh
    return !!group.audio_url
  }, [language])

  const goToNextSegment = (autoPlay: boolean) => {
    const groupIndex = currentGroupIndexRef.current
    const segmentIndex = currentSegmentIndexRef.current

    hasInteractedRef.current = true

    // Find next playable segment or section header
    for (let gi = groupIndex; gi < groups.length; gi++) {
      const group = groups[gi]

      // Section headers are playable at group level
      if (group.is_section_header && gi > groupIndex && groupHasAudio(group)) {
        currentGroupIndexRef.current = gi
        currentSegmentIndexRef.current = 0
        setCurrentGroupIndex(gi)
        setCurrentSegmentIndex(0)
        shouldAutoPlayRef.current = autoPlay
        return
      }

      const startSi = gi === groupIndex ? segmentIndex + 1 : 0
      for (let si = startSi; si < group.segments.length; si++) {
        if (segmentHasAudio(group.segments[si])) {
          currentGroupIndexRef.current = gi
          currentSegmentIndexRef.current = si
          setCurrentGroupIndex(gi)
          setCurrentSegmentIndex(si)
          shouldAutoPlayRef.current = autoPlay
          return
        }
      }
    }
  }

  const goToPreviousSegment = (autoPlay: boolean) => {
    const groupIndex = currentGroupIndexRef.current
    const segmentIndex = currentSegmentIndexRef.current

    hasInteractedRef.current = true

    // Find previous playable segment or section header
    for (let gi = groupIndex; gi >= 0; gi--) {
      const group = groups[gi]

      // Check segments first (in reverse order)
      const startSi = gi === groupIndex ? segmentIndex - 1 : group.segments.length - 1
      for (let si = startSi; si >= 0; si--) {
        if (segmentHasAudio(group.segments[si])) {
          currentGroupIndexRef.current = gi
          currentSegmentIndexRef.current = si
          setCurrentGroupIndex(gi)
          setCurrentSegmentIndex(si)
          shouldAutoPlayRef.current = autoPlay
          return
        }
      }

      // Section headers are playable at group level (check after segments if moving to earlier group)
      if (group.is_section_header && gi < groupIndex && groupHasAudio(group)) {
        currentGroupIndexRef.current = gi
        currentSegmentIndexRef.current = 0
        setCurrentGroupIndex(gi)
        setCurrentSegmentIndex(0)
        shouldAutoPlayRef.current = autoPlay
        return
      }
    }
  }

  const handleVoiceCommand = (command: { name: string; args: Record<string, unknown> }) => {
    pendingVoiceQuestionRef.current = false
    voiceQuestionIndexRef.current = null
    voiceAnswerIndexRef.current = null
    voiceAnswerTextRef.current = ''

    switch (command.name) {
      case 'play':
        handlePlay()
        break
      case 'pause':
        handlePause()
        break
      case 'next':
      case 'next_segment':
        goToNextSegment(wasPlayingBeforeVoiceRef.current)
        break
      case 'previous':
      case 'previous_segment':
        goToPreviousSegment(wasPlayingBeforeVoiceRef.current)
        break
      case 'bookmark': {
        const currentGroup = groups[currentGroupIndex]
        const segment = currentGroup?.segments[currentSegmentIndex]
        if (segment) {
          performBookmark(segment)
        }
        resumeNewsletterAfterVoice()
        break
      }
      case 'rewind': {
        const seconds = Number(command.args.seconds ?? 5)
        if (audioRef.current) {
          audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - seconds)
        }
        resumeNewsletterAfterVoice()
        break
      }
      case 'forward': {
        const seconds = Number(command.args.seconds ?? 5)
        if (audioRef.current) {
          audioRef.current.currentTime = Math.min(
            audioRef.current.duration || Infinity,
            audioRef.current.currentTime + seconds
          )
        }
        resumeNewsletterAfterVoice()
        break
      }
      default:
        resumeNewsletterAfterVoice()
        break
    }
  }

  const handleAskQuestionWithAudio = async (audioBlob: Blob) => {
    if (!issueId || !groups[currentGroupIndex]) return

    // Add user message (placeholder while transcribing)
    const userMsg: ConversationMessage = {
      role: 'user',
      text: t('player.transcribing'),
      timestamp: Date.now()
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoadingAnswer(true)

    try {
      // Prepare FormData
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      formData.append('issue_id', issueId)
      formData.append('language', language)

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

      // Ensure panel is open (it should be)
      setSidePanelOpen(true)
      setSidePanelTab('qa')

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
        text: t('player.noAnswer'),
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
    if (qaAudioUrl && audioRef.current) {
      // Save newsletter state
      savedNewsletterPositionRef.current = audioRef.current.currentTime
      savedNewsletterDurationRef.current = duration
      savedNewsletterSrcRef.current = audioRef.current.src

      // Pause newsletter (just in case)
      audioRef.current.pause()

      // Switch to Q&A audio
      setIsPlayingQaAudio(true)
      isPlayingQaAudioRef.current = true
      setQaPlaybackFailed(false)
      audioRef.current.src = qaAudioUrl

      const playPromise = audioRef.current.play()
      if (playPromise) {
        playPromise.catch((e) => {
          if (import.meta.env.DEV) {
            console.error("QA Playback failed:", e)
          }
          setQaPlaybackFailed(true)
        })
      }
    }
  }, [qaAudioUrl])

  const handlePlayQaManually = () => {
    if (audioRef.current && qaAudioUrl) {
      audioRef.current.play().then(() => {
        setQaPlaybackFailed(false)
      }).catch(e => {
        if (import.meta.env.DEV) {
          console.error("Manual QA Playback failed:", e)
        }
      })
    }
  }

  const handleVoiceSpeechStart = () => {
    pauseNewsletterForVoice(true)
    pendingVoiceQuestionRef.current = true
    voiceQuestionIndexRef.current = null
    voiceAnswerIndexRef.current = null
    voiceAnswerTextRef.current = ''
  }

  const handleVoiceSpeechEnd = () => {
    // Voice mode handles processing state internally
  }

  const handleVoiceTranscript = (text: string) => {
    pauseNewsletterForVoice()
    if (
      pendingVoiceQuestionRef.current ||
      (voiceQuestionIndexRef.current === null && voiceAnswerIndexRef.current === null)
    ) {
      addVoiceQuestionMessage()
      pendingVoiceQuestionRef.current = false
    }
    const mergedText = mergeTranscriptText(voiceAnswerTextRef.current, text)
    voiceAnswerTextRef.current = mergedText
    updateVoiceAnswerMessage(mergedText)
  }

  const handleVoiceAnswerStart = () => {
    pauseNewsletterForVoice()
  }

  const handleVoiceAnswerEnd = () => {
    resumeNewsletterAfterVoice(CONFIG.voiceMode.resumeDelayMs)
    pendingVoiceQuestionRef.current = false
    voiceQuestionIndexRef.current = null
    voiceAnswerIndexRef.current = null
    voiceAnswerTextRef.current = ''
  }

  const {
    isVoiceModeActive,
    isListening: isVoiceListening,
    isSpeaking: isVoiceSpeaking,
    isProcessing: isVoiceProcessing,
    lastCommand: lastVoiceCommand,
    toggleVoiceMode,
  } = useVoiceMode({
    issueId,
    onCommand: handleVoiceCommand,
    onSpeechStart: handleVoiceSpeechStart,
    onSpeechEnd: handleVoiceSpeechEnd,
    onTranscript: handleVoiceTranscript,
    onAnswerStart: handleVoiceAnswerStart,
    onAnswerEnd: handleVoiceAnswerEnd,
    onError: handleVoiceError,
  })

  useEffect(() => {
    if (isVoiceModeActive && isRecording) {
      stopRecording()
    }
  }, [isVoiceModeActive, isRecording, stopRecording])

  // Load issue, groups, and bookmarks
  useEffect(() => {
    async function loadData() {
      if (!issueId) return

      try {
        const { issue, groups } = await fetchIssueWithGroups(issueId)
        setIssue(issue)
        // Keep all groups; playback uses per-segment audio only
        setGroups(groups)

        // Load existing bookmarks
        try {
          const bookmarks = await fetchBookmarks(issueId)
          const bookmarkedIds = new Set(bookmarks.map(b => b.segment_id))
          setBookmarkedSegments(bookmarkedIds)
        } catch (err) {
          // Bookmarks table might not exist yet, silently ignore
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setError(message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [issueId])

  // Restore state logic
  useEffect(() => {
    if (restoredState && !loading && groups.length > 0) {
      // Validate indices
      if (restoredState.groupIndex < groups.length) {
        const group = groups[restoredState.groupIndex]
        if (restoredState.segmentIndex < group.segments.length) {
          setCurrentGroupIndex(restoredState.groupIndex)
          setCurrentSegmentIndex(restoredState.segmentIndex)
          hasInteractedRef.current = true // Allow auto-scroll
        }
      }
    }
  }, [restoredState, loading, groups])

  // Get current audio URL (per-segment or group-level for section headers, language-aware)
  const getCurrentAudio = () => {
    const group = groups[currentGroupIndex]
    if (!group) return null

    // Section headers have no segments - use group-level audio
    if (group.is_section_header) {
      if (language === 'zh') {
        return group.audio_url_zh || null
      }
      return group.audio_url || null
    }

    const segment = group.segments[currentSegmentIndex]
    if (!segment) return null

    // For Chinese, use audio_url_zh if available, otherwise skip this segment
    if (language === 'zh') {
      return segment.audio_url_zh || null
    }
    return segment.audio_url || null
  }

  const currentAudioUrl = getCurrentAudio()


  // Handle language switch mid-playback
  useEffect(() => {
    if (prevLanguageRef.current !== language && groups.length > 0) {
      prevLanguageRef.current = language

      // When switching to Chinese, check if current segment has Chinese audio
      if (language === 'zh') {
        const group = groups[currentGroupIndex]
        const segment = group?.segments[currentSegmentIndex]
        if (segment && !segment.audio_url_zh) {
          // Find next segment with Chinese audio
          let found = false
          for (let gi = currentGroupIndex; gi < groups.length && !found; gi++) {
            const g = groups[gi]
            const startSi = gi === currentGroupIndex ? currentSegmentIndex : 0
            for (let si = startSi; si < g.segments.length && !found; si++) {
              if (g.segments[si].audio_url_zh) {
                setCurrentGroupIndex(gi)
                setCurrentSegmentIndex(si)
                found = true
              }
            }
          }
          // If no Chinese audio found, reset to beginning
          if (!found) {
            setCurrentGroupIndex(0)
            setCurrentSegmentIndex(0)
          }
        }
      }

      // Force reload current audio with new language URL
      if (audioRef.current) {
        const wasPlaying = !audioRef.current.paused
        shouldAutoPlayRef.current = wasPlaying
        // Clear src to force reload
        audioRef.current.src = ''
      }
    }
  }, [language, groups, currentGroupIndex, currentSegmentIndex])

  // Set audio source when indices change
  useEffect(() => {
    if (audioRef.current && currentAudioUrl) {
      const audio = audioRef.current

      // Avoid reloading if URL hasn't changed (optimization)
      const currentSrc = audio.currentSrc || audio.src
      if (currentSrc === currentAudioUrl) {
        return
      }

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
      audio.src = currentAudioUrl
      audio.load()

      return () => {
        audio.removeEventListener('canplay', handleCanPlay)
      }
    }
  }, [currentAudioUrl, loading])

  // Update playback rate when speed changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  // Auto-scroll to current SEGMENT or SECTION HEADER (only after user interaction)
  useEffect(() => {
    if (!hasInteractedRef.current) return

    const currentGroup = groups[currentGroupIndex]
    if (currentGroup) {
      // Section headers scroll to the group element
      if (currentGroup.is_section_header) {
        const el = document.getElementById(`group-${currentGroup.id}`)
        if (el) {
          el.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
          })
        }
        return
      }

      // Regular groups scroll to the segment
      const currentSegment = currentGroup.segments[currentSegmentIndex]
      if (currentSegment) {
        const el = document.getElementById(`segment-${currentSegment.id}`)
        if (el) {
          el.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
          })
        }
      }
    }
  }, [currentGroupIndex, currentSegmentIndex, groups])

  const handleAudioError = (e: React.SyntheticEvent<HTMLAudioElement, Event>) => {
    const target = e.target as HTMLAudioElement
    // Only report error if we actually have a source
    if (target.src) {
      setError(`Audio playback failed: ${target.error?.message || 'Unknown error'}`)
      setIsPlaying(false)
    }
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
            // Don't show error immediately, user might just need to interact
            // setError(`Playback failed: ${err.message}`)
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
    if (isPlayingQaAudio) {
      // Q&A audio finished - restore newsletter
      setIsPlayingQaAudio(false)
      isPlayingQaAudioRef.current = false
      setQaAudioUrl(null)
      setQaPlaybackFailed(false)
      setIsResumingNewsletter(true)
      isResumingNewsletterRef.current = true

      // Delay before resuming
      setTimeout(() => {
        if (audioRef.current && savedNewsletterSrcRef.current) {
          audioRef.current.src = savedNewsletterSrcRef.current
          audioRef.current.currentTime = savedNewsletterPositionRef.current
          setDuration(savedNewsletterDurationRef.current)

          if (wasPlayingBeforeQa.current) {
            audioRef.current.play().catch(() => { })
          }
        }
        setIsResumingNewsletter(false)
        isResumingNewsletterRef.current = false
        // User requested auto-close panel after answer
        setSidePanelOpen(false)
      }, CONFIG.qa.resumeDelayMs)

      return
    }

    // Normal Playback Ended - find next playable segment or section header
    let found = false
    for (let gi = currentGroupIndex; gi < groups.length && !found; gi++) {
      const group = groups[gi]

      // Section headers are playable at group level
      if (group.is_section_header && gi > currentGroupIndex && groupHasAudio(group)) {
        setCurrentGroupIndex(gi)
        setCurrentSegmentIndex(0)
        shouldAutoPlayRef.current = true
        found = true
        break
      }

      const startSi = gi === currentGroupIndex ? currentSegmentIndex + 1 : 0
      for (let si = startSi; si < group.segments.length && !found; si++) {
        if (segmentHasAudio(group.segments[si])) {
          setCurrentGroupIndex(gi)
          setCurrentSegmentIndex(si)
          shouldAutoPlayRef.current = true
          found = true
        }
      }
    }

    if (!found) {
      // Finished all groups
      shouldAutoPlayRef.current = false
      setIsPlaying(false)
      clearState()
    }
  }


  // ... existing imports ...

  // ... inside component ...
  const lastTimeUpdateRef = useRef(0)

  const handleTimeUpdate = useCallback(() => {
    const now = Date.now()
    if (now - lastTimeUpdateRef.current < 250) return
    lastTimeUpdateRef.current = now

    // Only update main time if NOT playing QA audio and NOT resuming
    // Use refs to avoid race conditions/stale closures
    if (audioRef.current && !isPlayingQaAudioRef.current && !isResumingNewsletterRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }, [])

  const handleLoadedMetadata = () => {
    if (audioRef.current && !isPlayingQaAudioRef.current && !isResumingNewsletterRef.current) {
      setDuration(audioRef.current.duration)
    }
  }

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isPlayingQaAudioRef.current || isResumingNewsletterRef.current) return

    if (audioRef.current && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      audioRef.current.currentTime = percentage * duration
    }
  }

  // Segment Handling
  const handleSegmentClick = (groupIndex: number, segmentIndex: number) => {
    hasInteractedRef.current = true
    setCurrentGroupIndex(groupIndex)
    setCurrentSegmentIndex(segmentIndex)
    shouldAutoPlayRef.current = true
  }

  // Bookmark Handling
  const performBookmark = async (segment: Segment) => {
    if (!issueId || !issue) return

    // Check if already bookmarked
    if (bookmarkedSegments.has(segment.id)) {
      return
    }

    // Check if ClickUp is configured
    if (!isClickUpConfigured()) {
      setBookmarkError(t('player.clickupNotConfigured'))
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      if (import.meta.env.DEV) {
        console.error('Bookmark failed:', message)
      }
      setBookmarkError(message)
      setTimeout(() => setBookmarkError(null), 4000)
    } finally {
      setBookmarkingSegment(null)
    }
  }

  const handleBookmark = async (e: React.MouseEvent, segment: Segment) => {
    e.stopPropagation() // Don't trigger group click
    await performBookmark(segment)
  }

  // Sidebar Controls
  const handleOpenToc = () => {
    setSidePanelTab('toc')
    setSidePanelOpen(true)
  }

  const handleOpenQa = () => {
    setSidePanelTab('qa')
    setSidePanelOpen(true)
  }

  const handleGroupSelect = (groupIndex: number) => {
    setCurrentGroupIndex(groupIndex)
    setCurrentSegmentIndex(0)
    shouldAutoPlayRef.current = true
    setSidePanelOpen(false)

    // Scroll to group (optional, but good UX)
    // The auto-scroll effect might handle segments, but group headers?
    // Let's rely on standard scrolling to the group ID
    const group = groups[groupIndex]
    if (group) {
      const el = document.getElementById(`group-${group.id}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }

  const cyclePlaybackSpeed = () => {
    const currentIndex = PLAYBACK_SPEEDS.indexOf(playbackSpeed)
    const nextIndex = (currentIndex + 1) % PLAYBACK_SPEEDS.length
    setPlaybackSpeed(PLAYBACK_SPEEDS[nextIndex])
  }

  if (loading) {
    return <Loading message={t('player.loadingNewsletter')} />
  }

  if (error) {
    return (
      <div className="player-error">
        <Link to="/" className="back-link">&larr; {t('common.back')}</Link>
        <div className="error-container">
          <div className="error-icon">!</div>
          <p className="error-message">{t('player.loadFailed')}</p>
          <p className="error-detail">{error}</p>
          <button className="retry-btn" onClick={() => window.location.reload()}>
            {t('common.tryAgain')}
          </button>
        </div>
      </div>
    )
  }

  if (!issue) {
    return (
      <div className="player-error">
        <Link to="/" className="back-link">&larr; {t('common.back')}</Link>
        <div className="error-container">
          <div className="error-icon">?</div>
          <p className="error-message">{t('player.notFound')}</p>
          <Link to="/" className="retry-btn">{t('player.goHome')}</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="player">
      <header className="player-header">
        <div className="header-nav">
          <Link to="/" className="back-link">&larr; {t('common.back')}</Link>
          <Link to="/settings" className="settings-link" title={t('common.settings')}>⚙️</Link>
        </div>
        <h1>{issue.title}</h1>
        {issue.published_at && (
          <p className="published-date">
            {new Date(issue.published_at).toLocaleDateString(t('dates.locale'), {
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

      {voiceError && (
        <div className="voice-error-toast">
          <span className="toast-icon">🎙️</span>
          <span>{voiceError}</span>
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

      <SegmentList
        groups={groups}
        currentGroupIndex={currentGroupIndex}
        currentSegmentIndex={currentSegmentIndex}
        bookmarkedSegments={bookmarkedSegments}
        bookmarkingSegment={bookmarkingSegment}
        onSegmentClick={handleSegmentClick}
        onBookmark={handleBookmark}
        language={language}
      />

      <SidePanel
        isOpen={sidePanelOpen}
        activeTab={sidePanelTab}
        onClose={() => setSidePanelOpen(false)}
        onTabChange={setSidePanelTab}
        groups={groups}
        currentGroupIndex={currentGroupIndex}
        onGroupSelect={handleGroupSelect}
        messages={messages}
        isRecording={isRecording}
        isLoadingAnswer={isLoadingAnswer}
        recorderError={recorderError}
        voiceModeActive={isVoiceModeActive}
        voiceListening={isVoiceListening}
        voiceSpeaking={isVoiceSpeaking}
        voiceProcessing={isVoiceProcessing}
        lastVoiceCommand={lastVoiceCommand}
        isResumingNewsletter={isResumingNewsletter}
        qaPlaybackFailed={qaPlaybackFailed}
        onPlayQaManually={handlePlayQaManually}
      />

      <AudioBar
        isPlaying={isPlaying}
        currentTime={currentTime}
        duration={duration}
        playbackSpeed={playbackSpeed}
        isRecording={isRecording}
        isVoiceModeActive={isVoiceModeActive}
        isVoiceListening={isVoiceListening}
        isVoiceSpeaking={isVoiceSpeaking}
        lastVoiceCommand={lastVoiceCommand}
        onPlayPause={handlePlayPause}
        onProgressClick={handleProgressClick}
        onSpeedCycle={cyclePlaybackSpeed}
        onMicClick={handleMicClick}
        onVoiceToggle={toggleVoiceMode}
        onOpenToc={handleOpenToc}
        onOpenQa={handleOpenQa}
        groupsLength={groups.length}
        currentGroupIndex={currentGroupIndex}
        disabled={groups.length === 0}
      />

    </div>
  )
}
