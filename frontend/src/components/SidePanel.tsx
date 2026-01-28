import { TopicGroup, ConversationMessage } from '../types'
import { X, Play } from 'lucide-react'
import './SidePanel.css'

interface SidePanelProps {
    isOpen: boolean
    activeTab: 'toc' | 'qa'
    onClose: () => void
    onTabChange: (tab: 'toc' | 'qa') => void
    groups: TopicGroup[]
    currentGroupIndex: number
    onGroupSelect: (groupIndex: number) => void
    messages: ConversationMessage[]
    isRecording: boolean
    isLoadingAnswer: boolean
    recorderError: string | null
    voiceModeActive: boolean
    voiceListening: boolean
    voiceSpeaking: boolean
    voiceProcessing: boolean
    lastVoiceCommand: string | null
    isResumingNewsletter: boolean
    qaPlaybackFailed: boolean
    onPlayQaManually: () => void
}

export default function SidePanel({
    isOpen,
    activeTab,
    onClose,
    onTabChange,
    groups,
    currentGroupIndex,
    onGroupSelect,
    messages,
    isRecording,
    isLoadingAnswer,
    recorderError,
    voiceModeActive,
    voiceListening,
    voiceSpeaking,
    voiceProcessing,
    lastVoiceCommand,
    isResumingNewsletter,
    qaPlaybackFailed,
    onPlayQaManually
}: SidePanelProps) {

    if (!isOpen) return null

    return (
        <>
            <div className="side-panel-scrim" onClick={onClose} />
            <div className="side-panel">
                <div className="side-panel-header">
                    <div className="side-panel-tabs">
                        <button
                            className={`tab-btn ${activeTab === 'toc' ? 'active' : ''}`}
                            onClick={() => onTabChange('toc')}
                        >
                            Contents
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'qa' ? 'active' : ''}`}
                            onClick={() => onTabChange('qa')}
                        >
                            Q&A
                        </button>
                    </div>
                    <button className="close-panel-btn" onClick={onClose} aria-label="Close">
                        <X size={24} />
                    </button>
                </div>

                <div className="side-panel-content">
                    {activeTab === 'toc' && (
                        <div className="toc-list">
                            {groups.map((group, index) => (
                                <div
                                    key={group.id}
                                    className={`toc-item ${index === currentGroupIndex ? 'active' : ''}`}
                                    onClick={() => onGroupSelect(index)}
                                >
                                    <span className="toc-title">{group.label || 'Untitled Section'}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {activeTab === 'qa' && (
                        <div className="qa-messages-container">
                            {voiceModeActive && (
                                <div className="voice-status-card">
                                    <div className="voice-status-row">
                                        <span className={`voice-status-dot ${voiceListening ? 'on' : ''}`} />
                                        <span className="voice-status-label">
                                            {voiceSpeaking
                                                ? 'Listening...'
                                                : voiceProcessing
                                                    ? 'Processing...'
                                                    : voiceListening
                                                        ? 'Voice mode ready'
                                                        : 'Connecting...'}
                                        </span>
                                    </div>
                                    {lastVoiceCommand && (
                                        <div className="voice-status-command">
                                            Last command: {lastVoiceCommand}
                                        </div>
                                    )}
                                </div>
                            )}

                            {messages.length === 0 && !isRecording && !voiceModeActive && (
                                <p className="qa-placeholder">Tap the mic button in the audio bar to ask a question about this newsletter.</p>
                            )}

                            {/* Fallback Play Button */}
                            {qaPlaybackFailed && (
                                <div className="qa-message assistant error-fallback">
                                    <p>Auto-play blocked by browser. Tap to listen:</p>
                                    <button className="qa-play-button" onClick={onPlayQaManually}>
                                        <Play size={16} style={{ marginRight: 6 }} /> Play Answer
                                    </button>
                                </div>
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
                            {isResumingNewsletter && (
                                <div className="qa-message resuming">
                                    <p>Resuming newsletter...</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </>
    )
}
