import { TopicGroup, ConversationMessage } from '../types'
import { X, Play } from 'lucide-react'
import { useLanguage } from '../i18n'
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
    const { t, language } = useLanguage()

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
                            {t('sidePanel.contents')}
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'qa' ? 'active' : ''}`}
                            onClick={() => onTabChange('qa')}
                        >
                            {t('sidePanel.qa')}
                        </button>
                    </div>
                    <button className="close-panel-btn" onClick={onClose} aria-label={t('common.close')}>
                        <X size={24} />
                    </button>
                </div>

                <div className="side-panel-content">
                    {activeTab === 'toc' && (
                        <div className="toc-list">
                            {groups.map((group, index) => {
                                const displayLabel = language === 'zh' && group.label_zh
                                    ? group.label_zh
                                    : group.label
                                return (
                                    <div
                                        key={group.id}
                                        className={`toc-item ${index === currentGroupIndex ? 'active' : ''}`}
                                        onClick={() => onGroupSelect(index)}
                                    >
                                        <span className="toc-title">{displayLabel || t('sidePanel.untitledSection')}</span>
                                    </div>
                                )
                            })}
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
                                                ? t('sidePanel.listening')
                                                : voiceProcessing
                                                    ? t('sidePanel.processing')
                                                    : voiceListening
                                                        ? t('sidePanel.voiceReady')
                                                        : t('sidePanel.connecting')}
                                        </span>
                                    </div>
                                    {lastVoiceCommand && (
                                        <div className="voice-status-command">
                                            {t('sidePanel.lastCommand', { command: lastVoiceCommand })}
                                        </div>
                                    )}
                                </div>
                            )}

                            {messages.length === 0 && !isRecording && !voiceModeActive && (
                                <p className="qa-placeholder">{t('sidePanel.qaPlaceholder')}</p>
                            )}

                            {/* Fallback Play Button */}
                            {qaPlaybackFailed && (
                                <div className="qa-message assistant error-fallback">
                                    <p>{t('sidePanel.autoPlayBlocked')}</p>
                                    <button className="qa-play-button" onClick={onPlayQaManually}>
                                        <Play size={16} style={{ marginRight: 6 }} /> {t('sidePanel.playAnswer')}
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
                                    <p>{t('sidePanel.recording')}</p>
                                </div>
                            )}
                            {isLoadingAnswer && (
                                <div className="qa-message assistant loading">
                                    <p>{t('sidePanel.thinking')}</p>
                                </div>
                            )}
                            {recorderError && (
                                <div className="qa-message error">
                                    <p>{t('common.error')}: {recorderError}</p>
                                </div>
                            )}
                            {isResumingNewsletter && (
                                <div className="qa-message resuming">
                                    <p>{t('sidePanel.resuming')}</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </>
    )
}
