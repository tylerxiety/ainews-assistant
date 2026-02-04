import { test, expect } from '@playwright/test';

/**
 * Test to reproduce the link duplication bug.
 *
 * Bug description: When playing audio on the player page, link text like "StepFun"
 * gets duplicated infinitely, showing "StepFunStepFunStepFun..." instead of the
 * original content with properly linked text.
 *
 * The bug appears to be related to the renderContentWithLinks function in SegmentList.tsx
 * where link text replacement causes infinite duplication during playback.
 */

const TEST_URL = 'https://vicarly-subtransparent-reese.ngrok-free.dev';
const ISSUE_ID = '395517de-cd52-4bf9-8dac-ea0c3e55b3ce';

test.describe('Link Duplication Bug', () => {
  test('link text should not duplicate when playing audio', async ({ page }) => {
    // Navigate to the player page
    await page.goto(`${TEST_URL}/player/${ISSUE_ID}`);

    // Wait for segments to load
    await page.waitForSelector('.segment', { timeout: 30000 });

    // Find the segment containing "StepFun" content
    const stepFunSegment = page.locator('.segment-content:has-text("StepFun")').first();
    await expect(stepFunSegment).toBeVisible();

    // Get the initial text content before playing
    const initialText = await stepFunSegment.textContent();
    console.log('Initial text:', initialText?.substring(0, 200));

    // Verify the text doesn't have duplicate "StepFun" patterns initially
    // Count occurrences of "StepFun" - should match what's in the original content
    const initialStepFunCount = (initialText?.match(/StepFun/g) || []).length;
    console.log('Initial StepFun count:', initialStepFunCount);

    // The original content has "StepFun" appearing 4 times max
    expect(initialStepFunCount).toBeLessThanOrEqual(10);

    // Click play button
    const playButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await playButton.click();

    // Wait for playback to start and some time updates to occur
    await page.waitForTimeout(3000);

    // Get the text content after playing
    const afterPlayText = await stepFunSegment.textContent();
    console.log('After play text:', afterPlayText?.substring(0, 200));

    // Count StepFun occurrences after playback
    const afterPlayStepFunCount = (afterPlayText?.match(/StepFun/g) || []).length;
    console.log('After play StepFun count:', afterPlayStepFunCount);

    // The bug causes infinite duplication - count should not explode
    expect(afterPlayStepFunCount).toBeLessThanOrEqual(10);

    // The text should remain stable - not grow exponentially
    expect(afterPlayStepFunCount).toBe(initialStepFunCount);
  });

  test('segment content length should remain stable during playback', async ({ page }) => {
    await page.goto(`${TEST_URL}/player/${ISSUE_ID}`);

    await page.waitForSelector('.segment', { timeout: 30000 });

    // Get initial total length of all segment content
    const getContentLength = async () => {
      const contents = await page.locator('.segment-content').allTextContents();
      return contents.join('').length;
    };

    const initialLength = await getContentLength();
    console.log('Initial content length:', initialLength);

    // Start playback
    const playButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await playButton.click();

    // Check content length multiple times during playback
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(1000);
      const currentLength = await getContentLength();
      console.log(`Content length at ${i + 1}s:`, currentLength);

      // Content length should not grow significantly (allow 10% variance for dynamic content)
      expect(currentLength).toBeLessThan(initialLength * 1.1);
    }
  });
});
