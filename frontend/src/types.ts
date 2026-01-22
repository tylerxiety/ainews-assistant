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
    topic_group_id?: string
    order_index: number
    content_raw: string
    links?: SegmentLink[]
    audio_url?: string
    segment_type: 'section_header' | 'item' | 'topic_header'
    // Allow for other fields from DB
    [key: string]: any
}

export interface TopicGroup {
    id: string
    issue_id: string
    label: string
    audio_url?: string
    audio_duration_ms?: number
    order_index: number
    segments: Segment[]
    created_at?: string
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

export interface ConversationMessage {
    role: 'user' | 'assistant';
    text: string;
    audioUrl?: string;
    timestamp: number;
}
