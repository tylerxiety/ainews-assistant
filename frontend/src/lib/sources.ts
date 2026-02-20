export const NEWSLETTER_SOURCES = {
  ainews:        { id: 'ainews',        name: 'AINews',        color: '#ff8c42' },
  the_batch:     { id: 'the_batch',     name: 'The Batch',     color: '#4285f4' },
  tongyi_weekly: { id: 'tongyi_weekly', name: 'Tongyi Weekly',  color: '#34a853' },
} as const

export function getSourceInfo(sourceId: string | null | undefined) {
  return NEWSLETTER_SOURCES[(sourceId ?? 'ainews') as keyof typeof NEWSLETTER_SOURCES]
    ?? NEWSLETTER_SOURCES.ainews
}

export const ALL_SOURCES = 'all' as const
