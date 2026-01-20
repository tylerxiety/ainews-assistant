# User Guide

## ClickUp Integration

The AINews Assistant allows you to bookmark interesting news segments directly to your ClickUp workspace. This requires a one-time setup of your ClickUp API credentials in the app settings.

### Prerequisites

1.  A ClickUp account.
2.  A List in ClickUp where you want bookmarks to be created (e.g., a "To Read" or "Bookmarks" list).

### Setup Steps

1.  **Get your Personal Access Token:**
    *   Log in to ClickUp.
    *   Click your avatar in the lower-left corner.
    *   Select **Apps**.
    *   Under **API Token**, click **Generate** (or copy your existing token).
    *   *Note: Treat this token like a password.*

2.  **Get your List ID:**
    *   Navigate to the List you want to use in ClickUp.
    *   Look at the URL in your browser. It will look like `https://app.clickup.com/12345/v/l/li/90123456...`.
    *   The List ID is the number starting with `li` (e.g., `90123456`). If there is no `li`, look for the number after the last slash in the folder view, or use the ClickUp API to find it.
    *   *Alternative:* You can right-click the List in the sidebar, copy the link, and extract the ID from there.

3.  **Configure the App:**
    *   Open the **AINews Assistant** app.
    *   Click the **Settings** (gear) icon in the top navigation.
    *   Paste your **API Token** into the "ClickUp API Token" field.
    *   Paste your **List ID** into the "ClickUp List ID" field.
    *   Click **Save**.

### How to Bookmark

1.  Open any newsletter issue in the player.
2.  Listen to the audio or read the text.
3.  When you hear/see something interesting, tap the **Bookmark** icon (bookmark outline) next to the segment text.
4.  The icon will turn solid, indicating the segment has been saved to your ClickUp list as a new task.
5.  The task description will contain the text of the segment and the first link found in that segment.
