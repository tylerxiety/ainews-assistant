/**
 * ClickUp API integration for bookmarking newsletter segments
 */
import { ClickUpSettings, Segment } from '../types'

const STORAGE_KEY = 'clickup_settings'

/**
 * Get ClickUp settings from localStorage
 */
export function getClickUpSettings(): ClickUpSettings | null {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return null

    try {
        const settings = JSON.parse(stored)
        if (settings.apiToken && settings.listId) {
            return settings as ClickUpSettings
        }
        return null
    } catch {
        return null
    }
}

/**
 * Save ClickUp settings to localStorage
 */
export function saveClickUpSettings(apiToken: string, listId: string): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ apiToken, listId }))
}

/**
 * Clear ClickUp settings from localStorage
 */
export function clearClickUpSettings(): void {
    localStorage.removeItem(STORAGE_KEY)
}

/**
 * Check if ClickUp is configured
 */
export function isClickUpConfigured(): boolean {
    return getClickUpSettings() !== null
}

/**
 * Create a task in ClickUp from a newsletter segment
 */
interface ClickUpTaskResponse {
    id: string
    name: string
    url: string
}

export async function createClickUpTask(segment: Segment, issueTitle: string): Promise<ClickUpTaskResponse> {
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
        segment.links.forEach((link: { text?: string, url: string }) => {
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
