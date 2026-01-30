import { useState, useEffect, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import {
    getClickUpSettings,
    saveClickUpSettings,
    clearClickUpSettings,
} from '../lib/clickup'
import { useLanguage, Language } from '../i18n'
import './Settings.css'

export default function Settings() {
    const { language, setLanguage, t, tArray } = useLanguage()
    const [apiToken, setApiToken] = useState('')
    const [listId, setListId] = useState('')
    const [isConfigured, setIsConfigured] = useState(false)
    const [showToken, setShowToken] = useState(false)
    const [saveStatus, setSaveStatus] = useState<'saved' | 'cleared' | null>(null)

    // Load existing settings on mount
    useEffect(() => {
        const settings = getClickUpSettings()
        if (settings) {
            setApiToken(settings.apiToken)
            setListId(settings.listId)
            setIsConfigured(true)
        }
    }, [])

    const handleSave = (e: FormEvent) => {
        e.preventDefault()

        if (!apiToken.trim() || !listId.trim()) {
            return
        }

        saveClickUpSettings(apiToken.trim(), listId.trim())
        setIsConfigured(true)
        setSaveStatus('saved')

        // Clear status after a moment
        setTimeout(() => setSaveStatus(null), 2000)
    }

    const handleClear = () => {
        clearClickUpSettings()
        setApiToken('')
        setListId('')
        setIsConfigured(false)
        setShowToken(false)
        setSaveStatus('cleared')

        setTimeout(() => setSaveStatus(null), 2000)
    }

    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setLanguage(e.target.value as Language)
    }

    return (
        <div className="settings">
            <header className="settings-header">
                <Link to="/" className="back-link">&larr; {t('common.back')}</Link>
                <h1>{t('settings.title')}</h1>
            </header>

            <section className="settings-section">
                <h2>
                    <span className="section-icon">🌐</span>
                    {t('settings.language')}
                </h2>
                <p className="section-description">
                    {t('settings.languageDescription')}
                </p>
                <div className="form-group">
                    <select
                        value={language}
                        onChange={handleLanguageChange}
                        className="language-select"
                    >
                        <option value="en">{t('settings.english')}</option>
                        <option value="zh">{t('settings.chinese')}</option>
                    </select>
                </div>
            </section>

            <section className="settings-section">
                <h2>
                    <span className="section-icon">📌</span>
                    {t('settings.clickupTitle')}
                </h2>
                <p className="section-description">
                    {t('settings.clickupDescription')}
                </p>

                <form onSubmit={handleSave} className="settings-form">
                    <div className="form-group">
                        <label htmlFor="apiToken">{t('settings.apiToken')}</label>
                        <div className="input-with-toggle">
                            <input
                                id="apiToken"
                                type={showToken ? 'text' : 'password'}
                                value={apiToken}
                                onChange={(e) => setApiToken(e.target.value)}
                                placeholder={t('settings.apiTokenPlaceholder')}
                                autoComplete="off"
                            />
                            <button
                                type="button"
                                className="toggle-visibility"
                                onClick={() => setShowToken(!showToken)}
                                title={showToken ? t('settings.hideToken') : t('settings.showToken')}
                            >
                                {showToken ? '🙈' : '👁️'}
                            </button>
                        </div>
                        <p className="form-hint">
                            {t('settings.apiTokenHint')}
                        </p>
                    </div>

                    <div className="form-group">
                        <label htmlFor="listId">{t('settings.listId')}</label>
                        <input
                            id="listId"
                            type="text"
                            value={listId}
                            onChange={(e) => setListId(e.target.value)}
                            placeholder={t('settings.listIdPlaceholder')}
                            autoComplete="off"
                        />
                        <p className="form-hint">
                            {t('settings.listIdHint')}
                        </p>
                    </div>

                    <div className="form-actions">
                        <button
                            type="submit"
                            className="save-btn"
                            disabled={!apiToken.trim() || !listId.trim()}
                        >
                            💾 {t('settings.saveSettings')}
                        </button>

                        {isConfigured && (
                            <button
                                type="button"
                                className="clear-btn"
                                onClick={handleClear}
                            >
                                🗑️ {t('settings.clearSettings')}
                            </button>
                        )}
                    </div>

                    {saveStatus && (
                        <div className={`save-status ${saveStatus}`}>
                            {saveStatus === 'saved' && `✓ ${t('settings.settingsSaved')}`}
                            {saveStatus === 'cleared' && `✓ ${t('settings.settingsCleared')}`}
                        </div>
                    )}
                </form>

                {isConfigured && (
                    <div className="config-status configured">
                        <span className="status-icon">✓</span>
                        <span>{t('settings.clickupConnected')}</span>
                    </div>
                )}

                {!isConfigured && (
                    <div className="config-status not-configured">
                        <span className="status-icon">○</span>
                        <span>{t('settings.clickupNotConfigured')}</span>
                    </div>
                )}
            </section>

            <section className="settings-section help-section">
                <h2>
                    <span className="section-icon">❓</span>
                    {t('settings.helpTitle')}
                </h2>

                <div className="help-steps">
                    <div className="help-step">
                        <h3>{t('settings.getApiToken')}</h3>
                        <ol>
                            {tArray('settings.getApiTokenSteps').map((step, idx) => (
                                <li key={idx}>{step}</li>
                            ))}
                        </ol>
                    </div>

                    <div className="help-step">
                        <h3>{t('settings.getListId')}</h3>
                        <ol>
                            {tArray('settings.getListIdSteps').map((step, idx) => (
                                <li key={idx}>{step}</li>
                            ))}
                        </ol>
                    </div>
                </div>
            </section>
        </div>
    )
}
