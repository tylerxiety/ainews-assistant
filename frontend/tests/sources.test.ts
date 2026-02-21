import { describe, it, expect } from 'vitest'
import { getSourceInfo, ALL_SOURCES, NEWSLETTER_SOURCES } from '../src/lib/sources'

describe('getSourceInfo', () => {
  it('returns ainews info', () => {
    const info = getSourceInfo('ainews')
    expect(info.id).toBe('ainews')
    expect(info.name).toBe('AINews')
    expect(info.color).toBe('#ff8c42')
  })

  it('returns the_batch info', () => {
    const info = getSourceInfo('the_batch')
    expect(info.id).toBe('the_batch')
    expect(info.name).toBe('The Batch')
  })

  it('returns tongyi_weekly info', () => {
    const info = getSourceInfo('tongyi_weekly')
    expect(info.id).toBe('tongyi_weekly')
    expect(info.name).toBe('Tongyi Weekly')
  })

  it('falls back to ainews for null', () => {
    const info = getSourceInfo(null)
    expect(info.id).toBe('ainews')
  })

  it('falls back to ainews for undefined', () => {
    const info = getSourceInfo(undefined)
    expect(info.id).toBe('ainews')
  })

  it('falls back to ainews for unknown source', () => {
    const info = getSourceInfo('nonexistent')
    expect(info.id).toBe('ainews')
  })
})

describe('ALL_SOURCES', () => {
  it('equals "all"', () => {
    expect(ALL_SOURCES).toBe('all')
  })
})
