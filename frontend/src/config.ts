/**
 * Frontend Configuration
 * ======================
 * Loads configuration from the shared /config.yaml file.
 * 
 * To find settings:
 *   - Frontend behavior → this file (loaded from config.yaml)
 *   - AI models & backend → config.yaml → backend section
 *   - Secrets → backend/.env
 */

import rawConfig from '../../config.yaml'

// Type definitions for the config
interface FrontendConfig {
    playbackStateExpirationMs: number
    audioBar?: {
        showMicButton?: boolean
    }
    qa: {
        resumeDelayMs: number
        maxRecordingDurationMs: number
    }
}

interface VoiceModeConfig {
    model: string
    region: string
    sessionTimeoutMs: number
    vadSensitivity: {
        positiveSpeechThreshold: number
        negativeSpeechThreshold: number
        minSpeechFrames: number
    }
    resumeDelayMs: number
}

interface Config {
    frontend: FrontendConfig
    voiceMode: VoiceModeConfig
}

const config = rawConfig as unknown as Config

/**
 * Frontend configuration object
 */
export const CONFIG = {
    /** State persistence expiration in ms (24 hours) */
    playbackStateExpirationMs: config.frontend.playbackStateExpirationMs,
    audioBar: {
        /** Whether to show the manual Q&A mic button in the audio bar */
        showMicButton: config.frontend.audioBar?.showMicButton ?? true,
    },
    qa: {
        /** Delay in ms before resuming newsletter after Q&A answer ends */
        resumeDelayMs: config.frontend.qa.resumeDelayMs,
        /** Maximum duration for recording a question in ms */
        maxRecordingDurationMs: config.frontend.qa.maxRecordingDurationMs,
    },
    voiceMode: {
        model: config.voiceMode.model,
        region: config.voiceMode.region,
        sessionTimeoutMs: config.voiceMode.sessionTimeoutMs,
        vadSensitivity: config.voiceMode.vadSensitivity,
        resumeDelayMs: config.voiceMode.resumeDelayMs,
    },
}
