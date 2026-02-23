export const NEWSLETTER_SOURCES = {
  ainews:        { id: 'ainews',        name: 'AINews',        color: '#ff8c42' },
  the_batch:     { id: 'the_batch',     name: 'The Batch',     color: '#4285f4' },
  tongyi_weekly:   { id: 'tongyi_weekly',   name: 'Tongyi Weekly',   color: '#34a853' },
  import_ai:       { id: 'import_ai',       name: 'Import AI',       color: '#9b59b6' },
  last_week_in_ai: { id: 'last_week_in_ai', name: 'Last Week in AI', color: '#e74c3c' },
  the_sequence:    { id: 'the_sequence',     name: 'TheSequence',     color: '#f39c12' },
  interconnects:   { id: 'interconnects',    name: 'Interconnects',   color: '#1abc9c' },
  ahead_of_ai:    { id: 'ahead_of_ai',      name: 'Ahead of AI',     color: '#3498db' },
  normal_tech:     { id: 'normal_tech',      name: 'AI as Normal Tech', color: '#e67e22' },
  latent_space:    { id: 'latent_space',     name: 'Latent Space',    color: '#2ecc71' },
} as const

export function getSourceInfo(sourceId: string | null | undefined) {
  return NEWSLETTER_SOURCES[(sourceId ?? 'ainews') as keyof typeof NEWSLETTER_SOURCES]
    ?? NEWSLETTER_SOURCES.ainews
}

export const ALL_SOURCES = 'all' as const
