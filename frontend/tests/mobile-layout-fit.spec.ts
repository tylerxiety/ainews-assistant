import { expect, test, type Page } from '@playwright/test'

const ISSUE_PATH = '/player/946b4153-4685-42b5-83b7-ce06257e6df0'

type LayoutMetrics = {
  layoutViewportWidth: number
  visualViewportWidth: number
  viewportHeight: number
  scrollWidth: number
  overflowPixels: number
  horizontalScrollX: number
  audioRect: { left: number; right: number; top: number; bottom: number } | null
}

const readLayoutMetrics = async (page: Page): Promise<LayoutMetrics> => {
  return page.evaluate(() => {
    const scrollRoot = document.scrollingElement ?? document.documentElement
    const audioControls = document.querySelector('.audio-controls')
    const audioRect = audioControls?.getBoundingClientRect()
    const visualViewportWidth = window.visualViewport?.width ?? window.outerWidth

    return {
      layoutViewportWidth: window.innerWidth,
      visualViewportWidth,
      viewportHeight: window.innerHeight,
      scrollWidth: scrollRoot.scrollWidth,
      overflowPixels: Math.max(0, scrollRoot.scrollWidth - visualViewportWidth),
      horizontalScrollX: window.scrollX,
      audioRect: audioRect
        ? {
            left: audioRect.left,
            right: audioRect.right,
            top: audioRect.top,
            bottom: audioRect.bottom,
          }
        : null,
    }
  })
}

test.describe('mobile viewport fit', () => {
  test('player content fits viewport and audio bar is fully visible', async ({ page }) => {
    await page.goto(ISSUE_PATH)
    await page.waitForSelector('.segment', { timeout: 30_000 })
    await page.waitForSelector('.audio-controls', { timeout: 30_000 })

    const initialMetrics = await readLayoutMetrics(page)

    expect(initialMetrics.audioRect).not.toBeNull()
    expect(initialMetrics.audioRect!.left).toBeGreaterThanOrEqual(-1)
    expect(initialMetrics.audioRect!.right).toBeLessThanOrEqual(initialMetrics.visualViewportWidth + 1)
    expect(initialMetrics.audioRect!.bottom).toBeLessThanOrEqual(initialMetrics.viewportHeight + 1)

    // Layout viewport should match the visual viewport; if it grows, users need horizontal pan/zoom.
    expect(initialMetrics.layoutViewportWidth).toBeLessThanOrEqual(initialMetrics.visualViewportWidth + 1)

    // Mobile users should never need horizontal pan/zoom to read content or reach controls.
    expect(initialMetrics.overflowPixels).toBeLessThanOrEqual(1)

    await page.evaluate(() => window.scrollTo(240, window.scrollY))
    const afterHorizontalScrollAttempt = await readLayoutMetrics(page)
    expect(afterHorizontalScrollAttempt.horizontalScrollX).toBeLessThanOrEqual(1)
  })
})
