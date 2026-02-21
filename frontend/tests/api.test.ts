import { describe, it, expect, vi, beforeEach } from 'vitest'

describe('api module', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  async function importApi(envValue?: string) {
    if (envValue !== undefined) {
      vi.stubEnv('VITE_API_URL', envValue)
    }
    return await import('../src/lib/api')
  }

  it('apiUrl prepends localhost base URL by default', async () => {
    const { apiUrl } = await importApi()
    expect(apiUrl('/issues')).toBe('http://localhost:8080/issues')
  })

  it('apiUrl adds missing leading slash', async () => {
    const { apiUrl } = await importApi()
    expect(apiUrl('issues')).toBe('http://localhost:8080/issues')
  })

  it('with empty VITE_API_URL, produces relative URL', async () => {
    const { apiUrl } = await importApi('')
    expect(apiUrl('/issues')).toBe('/issues')
  })

  it('with custom VITE_API_URL, uses that base', async () => {
    const { apiUrl } = await importApi('https://api.example.com')
    expect(apiUrl('/issues')).toBe('https://api.example.com/issues')
  })
})
