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
    qa: {
        resumeDelayMs: number
        maxRecordingDurationMs: number
    }
}

interface Config {
    frontend: FrontendConfig
}

const config = rawConfig as unknown as Config

/**
 * Frontend configuration object
 */
export const CONFIG = {
    qa: {
        /** Delay in ms before resuming newsletter after Q&A answer ends */
        resumeDelayMs: config.frontend.qa.resumeDelayMs,
        /** Maximum duration for recording a question in ms */
        maxRecordingDurationMs: config.frontend.qa.maxRecordingDurationMs,
    },
}
