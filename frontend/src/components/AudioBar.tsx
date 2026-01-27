import { Play, Pause, Mic, MessageSquareText, List } from 'lucide-react'
import './AudioBar.css'

interface AudioBarProps {
    isPlaying: boolean
    currentTime: number
    duration: number
    playbackSpeed: number
    isRecording: boolean
    onPlayPause: () => void
    onProgressClick: (e: React.MouseEvent<HTMLDivElement>) => void
    onSpeedCycle: () => void
    onMicClick: () => void
    onOpenToc: () => void
    onOpenQa: () => void
    groupsLength: number
    currentGroupIndex: number
    disabled: boolean
}

export default function AudioBar({
    isPlaying,
    currentTime,
    duration,
    playbackSpeed,
    isRecording,
    onPlayPause,
    onProgressClick,
    onSpeedCycle,
    onMicClick,
    onOpenToc,
    onOpenQa,
    disabled
}: AudioBarProps) {

    const formatTime = (seconds: number) => {
        if (isNaN(seconds)) return '0:00'
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    return (
        <div className="audio-controls">
            {/* Row 1: Controls */}
            <div className="controls-row-main">
                <button
                    className="play-pause-btn"
                    onClick={onPlayPause}
                    disabled={disabled}
                    title={isPlaying ? "Pause" : "Play"}
                >
                    {isPlaying ? <Pause size={12} fill="currentColor" /> : <Play size={12} fill="currentColor" />}
                </button>

                <div className="time-display">
                    {formatTime(currentTime)} / {formatTime(duration)}
                </div>

                <div className="spacer" />

                <button className="control-btn speed-btn" onClick={onSpeedCycle} title="Playback Speed">
                    <span className="speed-text">{playbackSpeed}x</span>
                </button>

                <button
                    className={`control-btn mic-btn ${isRecording ? 'listening' : ''}`}
                    onClick={onMicClick}
                    title="Ask a question"
                >
                    <Mic size={20} />
                </button>

                <button
                    className="control-btn qa-btn"
                    onClick={onOpenQa}
                    title="Open Q&A"
                >
                    <MessageSquareText size={20} />
                </button>

                <button
                    className="control-btn toc-btn"
                    onClick={onOpenToc}
                    title="Table of Contents"
                >
                    <List size={20} />
                </button>
            </div>

            {/* Row 2: Progress */}
            <div className="progress-container" onClick={onProgressClick}>
                <div
                    className="progress-bar"
                    style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
                />
            </div>
        </div>
    )
}
