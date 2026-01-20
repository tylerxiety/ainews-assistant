import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    getClickUpSettings,
    saveClickUpSettings,
    clearClickUpSettings,
    isClickUpConfigured
} from '../lib/clickup'
import './Settings.css'

export default function Settings() {
    const [apiToken, setApiToken] = useState('')
    const [listId, setListId] = useState('')
    const [isConfigured, setIsConfigured] = useState(false)
    const [showToken, setShowToken] = useState(false)
    const [saveStatus, setSaveStatus] = useState(null) // 'saved', 'cleared', or null

    // Load existing settings on mount
    useEffect(() => {
        const settings = getClickUpSettings()
        if (settings) {
            setApiToken(settings.apiToken)
            setListId(settings.listId)
            setIsConfigured(true)
        }
    }, [])

    const handleSave = (e) => {
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

    return (
        <div className="settings">
            <header className="settings-header">
                <Link to="/" className="back-link">&larr; Back</Link>
                <h1>Settings</h1>
            </header>

            <section className="settings-section">
                <h2>
                    <span className="section-icon">📌</span>
                    ClickUp Integration
                </h2>
                <p className="section-description">
                    Connect to ClickUp to bookmark newsletter items as tasks.
                    Your credentials are stored locally in your browser.
                </p>

                <form onSubmit={handleSave} className="settings-form">
                    <div className="form-group">
                        <label htmlFor="apiToken">API Token</label>
                        <div className="input-with-toggle">
                            <input
                                id="apiToken"
                                type={showToken ? 'text' : 'password'}
                                value={apiToken}
                                onChange={(e) => setApiToken(e.target.value)}
                                placeholder="pk_12345678_..."
                                autoComplete="off"
                            />
                            <button
                                type="button"
                                className="toggle-visibility"
                                onClick={() => setShowToken(!showToken)}
                                title={showToken ? 'Hide token' : 'Show token'}
                            >
                                {showToken ? '🙈' : '👁️'}
                            </button>
                        </div>
                        <p className="form-hint">
                            Find it in ClickUp → Settings → Apps → API Token
                        </p>
                    </div>

                    <div className="form-group">
                        <label htmlFor="listId">List ID</label>
                        <input
                            id="listId"
                            type="text"
                            value={listId}
                            onChange={(e) => setListId(e.target.value)}
                            placeholder="987654321"
                            autoComplete="off"
                        />
                        <p className="form-hint">
                            Copy the list link and extract the last number
                        </p>
                    </div>

                    <div className="form-actions">
                        <button
                            type="submit"
                            className="save-btn"
                            disabled={!apiToken.trim() || !listId.trim()}
                        >
                            💾 Save Settings
                        </button>

                        {isConfigured && (
                            <button
                                type="button"
                                className="clear-btn"
                                onClick={handleClear}
                            >
                                🗑️ Clear Settings
                            </button>
                        )}
                    </div>

                    {saveStatus && (
                        <div className={`save-status ${saveStatus}`}>
                            {saveStatus === 'saved' && '✓ Settings saved successfully!'}
                            {saveStatus === 'cleared' && '✓ Settings cleared'}
                        </div>
                    )}
                </form>

                {isConfigured && (
                    <div className="config-status configured">
                        <span className="status-icon">✓</span>
                        <span>ClickUp is connected</span>
                    </div>
                )}

                {!isConfigured && (
                    <div className="config-status not-configured">
                        <span className="status-icon">○</span>
                        <span>ClickUp not configured</span>
                    </div>
                )}
            </section>

            <section className="settings-section help-section">
                <h2>
                    <span className="section-icon">❓</span>
                    How to Get Credentials
                </h2>

                <div className="help-steps">
                    <div className="help-step">
                        <h3>1. Get your API Token</h3>
                        <ol>
                            <li>Open <a href="https://app.clickup.com" target="_blank" rel="noopener noreferrer">ClickUp</a></li>
                            <li>Click your avatar (bottom-left) → <strong>Settings</strong></li>
                            <li>Click <strong>Apps</strong> in the sidebar</li>
                            <li>Scroll to <strong>API Token</strong> section</li>
                            <li>Click <strong>Generate</strong> or copy existing</li>
                        </ol>
                    </div>

                    <div className="help-step">
                        <h3>2. Get your List ID</h3>
                        <ol>
                            <li>Open the List where you want bookmarks</li>
                            <li>Click the <strong>⋮</strong> menu on the list</li>
                            <li>Select <strong>Copy link</strong></li>
                            <li>The URL looks like: <code>app.clickup.com/123/v/li/<strong>987654321</strong></code></li>
                            <li>The last number is your List ID</li>
                        </ol>
                    </div>
                </div>
            </section>
        </div>
    )
}
