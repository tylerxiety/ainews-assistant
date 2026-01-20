/**
 * ClickUp API integration for bookmarking newsletter segments
 */

const STORAGE_KEY = 'clickup_settings'
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8080'

/**
 * Get ClickUp settings from localStorage
 * @returns {{ apiToken: string, listId: string } | null}
 */
export function getClickUpSettings() {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return null

    try {
        const settings = JSON.parse(stored)
        if (settings.apiToken && settings.listId) {
            return settings
        }
        return null
    } catch (e) {
        console.warn('Invalid ClickUp settings in localStorage:', e)
        return null
    }
}

/**
 * Save ClickUp settings to localStorage
 * @param {string} apiToken - ClickUp API token
 * @param {string} listId - ClickUp list ID
 */
export function saveClickUpSettings(apiToken, listId) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ apiToken, listId }))
}

/**
 * Clear ClickUp settings from localStorage
 */
export function clearClickUpSettings() {
    localStorage.removeItem(STORAGE_KEY)
}

/**
 * Check if ClickUp is configured
 * @returns {boolean}
 */
export function isClickUpConfigured() {
    return getClickUpSettings() !== null
}

/**
 * Create a task in ClickUp from a newsletter segment
 * @param {Object} segment - The segment object from Supabase
 * @param {string} issueTitle - The newsletter issue title
 * @returns {Promise<Object>} - Created task data
 */
export async function createClickUpTask(segment, issueTitle) {
    const settings = getClickUpSettings()

    if (!settings) {
        throw new Error('ClickUp not configured. Please set up your API token and list ID in Settings.')
    }

    const { apiToken, listId } = settings

    // Build task name from segment content (truncated)
    const taskName = segment.content_raw.length > 100
        ? segment.content_raw.substring(0, 97) + '...'
        : segment.content_raw

    // Build description with full content and links
    let description = `**From Newsletter:** ${issueTitle}\n\n`
    description += `**Content:**\n${segment.content_raw}\n\n`

    if (segment.links && segment.links.length > 0) {
        description += '**Links:**\n'
        segment.links.forEach(link => {
            description += `- [${link.text || link.url}](${link.url})\n`
        })
    }

    // Call backend proxy to avoid CORS issues
    const response = await fetch(`${BACKEND_URL}/api/bookmark`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            api_token: apiToken,
            list_id: listId,
            task_name: taskName,
            description: description,
            tags: ['newsletter-bookmark'],
        }),
    })

    if (!response.ok) {
        let errorMsg = `HTTP ${response.status}`
        try {
            const errorData = await response.json()
            errorMsg = errorData.detail || errorData.error || errorMsg
        } catch (e) {
            console.warn('Failed to parse error response:', e)
        }
        throw new Error(`Failed to create bookmark: ${errorMsg}`)
    }

    return response.json()
}
