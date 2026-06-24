import React from 'react';
import { test, expect } from '@playwright/experimental-ct-react';
import DownloadQueuePage from '../../pages/DownloadQueuePage';

test.describe('DownloadQueuePage component actions', () => {
  test('renders empty state when no jobs are present', async ({ mount }) => {
    const component = await mount(<DownloadQueuePage />);
    await expect(component.locator('text=Geen downloads in de wachtrij')).toBeVisible();
  });

  // Placeholder for future action tests when UI supports pause/resume/cancel
  test('has placeholder for queue actions (to be implemented)', async ({ mount }) => {
    const component = await mount(<DownloadQueuePage />);
    // Ensure the component renders without errors
    await expect(component).toBeTruthy();
  });
});
