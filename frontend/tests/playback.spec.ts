import { test, expect } from '@playwright/test';

test.describe('Player Segment Playback & State Persistence', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app (assuming running on localhost:5173)
    await page.goto('http://localhost:5173');
    
    // Click on the first newsletter issue to enter the player
    // This assumes the issue list is rendered on the home page
    await page.locator('.issue-card').first().click();
    
    // Wait for player to load
    await page.waitForSelector('.player');
  });

  test('Scenario 1 & 2: Tap segment plays audio and switching segments works', async ({ page }) => {
    // Find first group and first segment
    const firstSegment = page.locator('.topic-group').nth(0).locator('.segment').nth(0);
    
    // Click it
    await firstSegment.click();
    
    // Verify it becomes active
    await expect(firstSegment).toHaveClass(/active/);
    
    // Check if audio is playing (this checks the state, not actual sound)
    const playButton = page.locator('.play-pause-btn');
    await expect(playButton).toHaveText('⏸'); // Pause symbol means playing
    
    // Click a segment in the second group (if exists)
    const secondGroupSegment = page.locator('.topic-group').nth(1).locator('.segment').nth(0);
    if (await secondGroupSegment.count() > 0) {
        await secondGroupSegment.click();
        await expect(secondGroupSegment).toHaveClass(/active/);
        await expect(firstSegment).not.toHaveClass(/active/);
    }
  });

  test('Scenario 6: Scroll does not trigger playback', async ({ page }) => {
    const segment = page.locator('.segment').first();
    
    // Perform a drag/scroll action on the segment
    const box = await segment.boundingBox();
    if (box) {
        await page.mouse.move(box.x + 5, box.y + 5);
        await page.mouse.down();
        await page.mouse.move(box.x + 5, box.y + 100); // Drag down 100px
        await page.mouse.up();
    }
    
    // Verify NOT active (didn't trigger click)
    await expect(segment).not.toHaveClass(/active/);
  });

  test('Scenario 5: State Persistence', async ({ page }) => {
    // Play the second segment
    const segmentToPlay = page.locator('.segment').nth(1);
    await segmentToPlay.click();
    await expect(segmentToPlay).toHaveClass(/active/);
    
    // Get the issue ID from URL to verify we return to same one
    const url = page.url();
    
    // Reload the page
    await page.reload();
    
    // Wait for player
    await page.waitForSelector('.player');
    
    // Verify the same segment is active
    const restoredSegment = page.locator('.segment').nth(1);
    await expect(restoredSegment).toHaveClass(/active/);
    
    // Verify auto-scroll (harder to test precisely, but we can check visibility)
    await expect(restoredSegment).toBeVisible();
  });
});
