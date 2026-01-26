import { useState, useEffect, useRef, useCallback } from 'react'
import { CONFIG } from '../config'

interface PlaybackState {
    issueId: string
    groupIndex: number
    segmentIndex: number
    savedAt: number
}

export function usePlaybackState(
    issueId: string | undefined,
    currentGroupIndex: number,
    currentSegmentIndex: number
) {
    const [restoredState, setRestoredState] = useState<PlaybackState | null>(null)
    const valuesRef = useRef({ issueId, currentGroupIndex, currentSegmentIndex })

    // Update refs whenever values change
    useEffect(() => {
        valuesRef.current = { issueId, currentGroupIndex, currentSegmentIndex }
    }, [issueId, currentGroupIndex, currentSegmentIndex])

    // Load state on mount
    useEffect(() => {
        if (!issueId) return

        try {
            const raw = localStorage.getItem('playback_state')
            if (raw) {
                const state = JSON.parse(raw) as PlaybackState
                
                // Check if valid for this issue
                if (state.issueId !== issueId) {
                    return
                }

                // Check expiration
                if (Date.now() - state.savedAt > CONFIG.playbackStateExpirationMs) {
                    localStorage.removeItem('playback_state')
                    return
                }

                setRestoredState(state)
            }
        } catch (e) {
            if (import.meta.env.DEV) {
                console.error("Failed to load playback state", e)
            }
        }
    }, [issueId])

    const saveState = useCallback(() => {
        const { issueId, currentGroupIndex, currentSegmentIndex } = valuesRef.current
        if (!issueId) return

        const state: PlaybackState = {
            issueId,
            groupIndex: currentGroupIndex,
            segmentIndex: currentSegmentIndex,
            savedAt: Date.now()
        }
        try {
            localStorage.setItem('playback_state', JSON.stringify(state))
        } catch {
            // localStorage may be unavailable in private browsing
        }
    }, [])

    const clearState = useCallback(() => {
        try {
            localStorage.removeItem('playback_state')
        } catch {
            // localStorage may be unavailable in private browsing
        }
    }, [])

    // Auto-save on visibility change and before unload
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                saveState()
            }
        }

        const handleBeforeUnload = () => {
            saveState()
        }

        document.addEventListener('visibilitychange', handleVisibilityChange)
        window.addEventListener('beforeunload', handleBeforeUnload)

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange)
            window.removeEventListener('beforeunload', handleBeforeUnload)
        }
    }, [saveState])

    // Save on unmount (SPA navigation)
    useEffect(() => {
        return () => {
            saveState()
        }
    }, [saveState])

    return { restoredState, clearState }
}
