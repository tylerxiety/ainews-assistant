import { expect, test } from '@playwright/test'

test('a recap section with embedded segments plays and advances on mobile', async ({ page }) => {
  await page.goto('/player/96c37a1e-4d7a-4a04-bc05-1ffd163ec5f6')
  await page.waitForFunction(() => Boolean(navigator.serviceWorker?.controller))

  const recap = page.locator('.section-header').filter({
    has: page.getByRole('heading', { name: 'AI Twitter Recap', exact: true }),
  })
  const audio = page.locator('audio')
  const first = recap.locator('.segment').nth(0)
  const second = recap.locator('.segment').nth(1)

  await recap.getByRole('heading').tap()
  await expect(first).toHaveClass(/\bactive\b/)
  await expect.poll(() => audio.evaluate(el => el.currentTime)).toBeGreaterThan(0)

  await audio.evaluate(el => { el.currentTime = el.duration - 0.2 })
  await expect(second).toHaveClass(/\bactive\b/)
  await expect(audio).toHaveAttribute('src', /group_2_segment_1\.mp3$/)
  await expect.poll(() => audio.evaluate(el => !el.paused && el.currentTime > 0)).toBe(true)

  await first.tap()
  await expect(first).toHaveClass(/\bactive\b/)
  await expect(audio).toHaveAttribute('src', /group_2_segment_0\.mp3$/)
  await expect.poll(() => audio.evaluate(el => !el.paused && el.currentTime > 0)).toBe(true)
})
