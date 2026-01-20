/**
 * ClickUp API integration for bookmarking newsletter segments
 */

const STORAGE_KEY = 'clickup_settings'

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
    } catch {
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

    // ClickUp API call
    const response = await fetch(`https://api.clickup.com/api/v2/list/${listId}/task`, {
        method: 'POST',
        headers: {
            'Authorization': apiToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: taskName,
            markdown_description: description,
            // Add tag for easy filtering
            tags: ['newsletter-bookmark'],
        }),
    })

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMsg = errorData.err || errorData.error || `HTTP ${response.status}`
        throw new Error(`ClickUp API error: ${errorMsg}`)
    }

    return response.json()
}
