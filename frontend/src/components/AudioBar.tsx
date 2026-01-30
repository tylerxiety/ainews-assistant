import { Play, Pause, Mic, MessageSquareText, List, AudioWaveform } from 'lucide-react'
import { useLanguage } from '../i18n'
import './AudioBar.css'

interface AudioBarProps {
    isPlaying: boolean
    currentTime: number
    duration: number
    playbackSpeed: number
    isRecording: boolean
    isVoiceModeActive: boolean
    isVoiceListening: boolean
    isVoiceSpeaking: boolean
    lastVoiceCommand: string | null
    onPlayPause: () => void
    onProgressClick: (e: React.MouseEvent<HTMLDivElement>) => void
    onSpeedCycle: () => void
    onMicClick: () => void
    onVoiceToggle: () => void
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
    isVoiceModeActive,
    isVoiceListening,
    isVoiceSpeaking,
    lastVoiceCommand,
    onPlayPause,
    onProgressClick,
    onSpeedCycle,
    onMicClick,
    onVoiceToggle,
    onOpenToc,
    onOpenQa,
    disabled
}: AudioBarProps) {
    const { t } = useLanguage()

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
                <div className="controls-left">
                    <button
                        className="play-pause-btn"
                        onClick={onPlayPause}
                        disabled={disabled}
                        title={isPlaying ? t('audioBar.pause') : t('audioBar.play')}
                    >
                        {isPlaying ? <Pause size={12} fill="currentColor" /> : <Play size={12} fill="currentColor" />}
                    </button>

                    <div className="time-display">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </div>

                    <button className="control-btn speed-btn" onClick={onSpeedCycle} title={t('audioBar.playbackSpeed')}>
                        <span className="speed-text">{playbackSpeed}x</span>
                    </button>
                </div>

                <div className="controls-center">
                    <button
                        className={`control-btn voice-toggle-btn ${isVoiceModeActive ? 'active' : ''} ${isVoiceSpeaking ? 'speaking' : ''}`}
                        onClick={onVoiceToggle}
                        title={isVoiceModeActive ? t('audioBar.disableVoice') : t('audioBar.enableVoice')}
                    >
                        <AudioWaveform size={20} />
                    </button>

                    {isVoiceModeActive && (
                        <div className="voice-status">
                            <span className={`voice-dot ${isVoiceListening ? 'on' : ''}`} />
                            <span className="voice-status-text">
                                {isVoiceSpeaking
                                    ? t('audioBar.voiceListening')
                                    : isVoiceListening
                                        ? t('audioBar.voiceOn')
                                        : t('audioBar.voiceConnecting')}
                            </span>
                            {lastVoiceCommand && (
                                <span className="voice-last-command">{t('audioBar.lastCommand', { command: lastVoiceCommand })}</span>
                            )}
                        </div>
                    )}
                </div>

                <div className="controls-right">
                    <button
                        className={`control-btn mic-btn ${isRecording ? 'listening' : ''}`}
                        onClick={onMicClick}
                        title={t('audioBar.askQuestion')}
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        className="control-btn qa-btn"
                        onClick={onOpenQa}
                        title={t('audioBar.openQa')}
                    >
                        <MessageSquareText size={20} />
                    </button>

                    <button
                        className="control-btn toc-btn"
                        onClick={onOpenToc}
                        title={t('audioBar.tableOfContents')}
                    >
                        <List size={20} />
                    </button>
                </div>
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
