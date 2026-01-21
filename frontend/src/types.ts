export interface Issue {
    id: string
    title: string
    published_at: string
    url?: string
    summary?: string
    // Allow for other fields from DB
    [key: string]: any
}

export interface SegmentLink {
    text?: string
    url: string
}

export interface Segment {
    id: string
    issue_id: string
    order_index: number
    content_raw: string
    links?: SegmentLink[]
    audio_url?: string
    // Allow for other fields from DB
    [key: string]: any
}

export interface Bookmark {
    id: string
    issue_id: string
    segment_id: string
    clickup_task_id: string
    created_at?: string
    [key: string]: any
}

export interface ClickUpSettings {
    apiToken: string
    listId: string
}
